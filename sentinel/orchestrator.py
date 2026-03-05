"""
Main orchestration loop: detect → repair (LangGraph) → PR.

Outer loop: plain Python while-True monitoring via Sentry.
Inner repair cycle: LangGraph StateGraph (mechanic → auditor → create_pr).
"""

import asyncio
import os
import subprocess
from datetime import datetime
from typing import Dict, Optional

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from sentinel.agents.auditor import Auditor
from sentinel.agents.mechanic import Mechanic
from sentinel.agents.sentry import Sentry
from sentinel.models import AuditReport, ProposalPackage
from sentinel.router import assess_problem


MAX_ITERATIONS = 3


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------


class RepairState(TypedDict):
    error_context: Dict
    model: str
    proposal: Optional[ProposalPackage]
    audit_report: Optional[AuditReport]
    audit_feedback: Optional[str]
    iteration: int
    pr_url: Optional[str]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------


async def mechanic_node(state: RepairState) -> dict:
    """Invoke the Mechanic to produce a ProposalPackage."""
    mechanic = Mechanic(model=state["model"])
    proposal = await mechanic.run(
        error_context=state["error_context"],
        audit_feedback=state.get("audit_feedback"),
        iteration=state["iteration"] + 1,
    )
    return {"proposal": proposal, "iteration": state["iteration"] + 1}


async def auditor_node(state: RepairState) -> dict:
    """Invoke the Auditor to review the current ProposalPackage."""
    auditor = Auditor()
    audit = await auditor.run(state["proposal"])
    feedback: Optional[str] = None
    if not audit.approved:
        findings = "\n".join(f"- {f}" for f in audit.findings)
        feedback = (
            f"Auditor rejected.\nFindings:\n{findings}\n"
            f"Recommendation: {audit.recommendation}"
        )
    return {"audit_report": audit, "audit_feedback": feedback}


async def create_pr_node(state: RepairState) -> dict:
    """Create a git branch and GitHub PR for the approved proposal."""
    pr_url = _create_pr(
        proposal=state["proposal"],
        audit_report=state["audit_report"],
        error_context=state["error_context"],
    )
    return {"pr_url": pr_url}


# ---------------------------------------------------------------------------
# Conditional edge routing
# ---------------------------------------------------------------------------


def route_after_audit(state: RepairState) -> str:
    """Route to create_pr, loop back to mechanic, or end on max iterations."""
    if state["audit_report"].approved:
        return "create_pr"
    if state["iteration"] >= MAX_ITERATIONS:
        print(
            f"[Orchestrator] Max iterations ({MAX_ITERATIONS}) reached without approval."
        )
        return END
    return "mechanic"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def _build_repair_graph() -> StateGraph:
    builder = StateGraph(RepairState)
    builder.add_node("mechanic", mechanic_node)
    builder.add_node("auditor", auditor_node)
    builder.add_node("create_pr", create_pr_node)

    builder.add_edge(START, "mechanic")
    builder.add_edge("mechanic", "auditor")
    builder.add_conditional_edges(
        "auditor",
        route_after_audit,
        {"mechanic": "mechanic", "create_pr": "create_pr", END: END},
    )
    builder.add_edge("create_pr", END)
    return builder.compile()


repair_graph = _build_repair_graph()


# ---------------------------------------------------------------------------
# PR creation helper
# ---------------------------------------------------------------------------


def _create_pr(
    proposal: ProposalPackage,
    audit_report: AuditReport,
    error_context: Dict,
) -> Optional[str]:
    """
    Create a git branch, commit changed files, push, and open a GitHub PR.
    Returns the PR URL or None if creation fails (soft failure).
    """
    error_type = str(error_context.get("type", "unknown")).replace(" ", "_").lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch = f"fix/{error_type}-{timestamp}"
    app_root = "/Users/hunterbetz/workspace/sentinel/toy_app"

    try:
        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=app_root,
            check=True,
            capture_output=True,
        )

        for changed_file in proposal.changed_files:
            subprocess.run(
                ["git", "add", changed_file.path],
                cwd=app_root,
                check=True,
                capture_output=True,
            )

        commit_msg = (
            f"fix({error_type}): autonomous patch (iter {proposal.iteration})\n\n"
            f"{proposal.mechanic_notes}"
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=app_root,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=app_root,
            check=True,
            capture_output=True,
        )

        pr_body = (
            f"## Summary\n\n"
            f"Autonomous fix for `{error_type}` (iteration {proposal.iteration}).\n\n"
            f"**Mechanic notes:** {proposal.mechanic_notes}\n\n"
            f"**Audit recommendation:** {audit_report.recommendation}\n\n"
            f"## Changed files\n\n"
            + "\n".join(f"- `{f.path}`" for f in proposal.changed_files)
            + "\n\n"
            "🤖 Generated with [Sentinel](https://github.com/anthropics/claude-code)"
        )
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                f"fix({error_type}): autonomous patch (iter {proposal.iteration})",
                "--body",
                pr_body,
            ],
            cwd=app_root,
            capture_output=True,
            text=True,
        )
        pr_url = result.stdout.strip()
        if pr_url:
            return pr_url
        print(f"[Orchestrator] gh pr create output: {result.stderr.strip()}")
        return None

    except subprocess.CalledProcessError as exc:
        print(f"[Orchestrator] PR creation failed: {exc}")
        return None
    except FileNotFoundError as exc:
        print(f"[Orchestrator] Required tool not found: {exc}")
        return None


# ---------------------------------------------------------------------------
# Outer monitoring loop
# ---------------------------------------------------------------------------


async def run() -> None:
    sentry = Sentry()
    while True:
        error_context = await sentry.run_audit(app_url=os.environ.get("SENTRY_URL"))
        if error_context.get("escalation") == "ESCALATE":
            model = assess_problem(error_context)
            print(f"[Orchestrator] Escalation detected — starting repair with {model}")
            result = await repair_graph.ainvoke(
                {
                    "error_context": error_context,
                    "model": model,
                    "proposal": None,
                    "audit_report": None,
                    "audit_feedback": None,
                    "iteration": 0,
                    "pr_url": None,
                },
                config={"recursion_limit": 20},
            )
            if result.get("pr_url"):
                print(f"[Orchestrator] PR created: {result['pr_url']}")
            else:
                print("[Orchestrator] Repair cycle ended without PR.")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run())
