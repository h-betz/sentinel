"""
Verifies the fix works and is safe.
Runs security scanning (bandit, SQL injection checks) and re-runs tests
to independently confirm the Mechanic's proposal before a PR is created.
"""

import subprocess
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from sentinel.models import AuditReport, ProposalPackage


@dataclass
class AuditorDeps:
    proposal: ProposalPackage
    app_root: str


class Auditor:

    def __init__(self, model: str = "anthropic:claude-sonnet-4-6"):
        self.agent = Agent(
            model,
            deps_type=AuditorDeps,
            output_type=AuditReport,
            system_prompt=(
                "You are an Auditor. Your job is to review a proposed code fix and determine "
                "whether it is safe and correct.\n\n"
                "Your review process:\n"
                "1. Read each changed file with read_file\n"
                "2. Run bandit security analysis with run_bandit on each changed file\n"
                "3. Check for SQL injection patterns with check_sql_injection on each file's content\n"
                "4. Re-run the test suite independently with run_tests\n\n"
                "Approve ONLY if ALL of the following are true:\n"
                "- Tests pass (run_tests exit code 0)\n"
                "- No HIGH severity bandit findings\n"
                "- No SQL injection patterns detected\n"
                "- changed_files is non-empty\n\n"
                "Return an AuditReport with:\n"
                "- approved: true only when all checks pass\n"
                "- findings: list of specific issues found (empty if clean)\n"
                "- recommendation: always populated — either 'Approved' or specific changes needed"
            ),
        )
        self._register_tools()

    def _register_tools(self) -> None:
        """Attach security and verification tools to the internal agent."""

        @self.agent.tool
        async def read_file(ctx: RunContext[AuditorDeps], path: str) -> str:
            """Read a changed file relative to app_root for review."""
            full_path = f"{ctx.deps.app_root}/{path}"
            with open(full_path, "r") as f:
                return f.read()

        @self.agent.tool
        async def run_bandit(ctx: RunContext[AuditorDeps], file_path: str) -> str:
            """Run bandit static security analysis on a file path relative to app_root."""
            full_path = f"{ctx.deps.app_root}/{file_path}"
            try:
                result = subprocess.run(
                    ["bandit", "-r", full_path, "-f", "text"],
                    capture_output=True,
                    text=True,
                )
                return result.stdout + result.stderr
            except FileNotFoundError:
                return (
                    "WARNING: bandit not installed — skipping static security analysis"
                )

        @self.agent.tool
        async def check_sql_injection(
            ctx: RunContext[AuditorDeps], content: str
        ) -> str:
            """Scan file content for common SQL injection patterns (f-strings, %-format, .format)."""
            patterns = [
                ('f"', "f-string SQL interpolation"),
                ("f'", "f-string SQL interpolation"),
                ("% (", "%-format SQL interpolation"),
                ('%" ', "%-format SQL interpolation"),
                (".format(", ".format() SQL interpolation"),
            ]
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WHERE", "FROM"]
            findings = []
            for line_num, line in enumerate(content.splitlines(), 1):
                line_upper = line.upper()
                has_sql = any(kw in line_upper for kw in sql_keywords)
                if has_sql:
                    for pattern, description in patterns:
                        if pattern in line:
                            findings.append(
                                f"Line {line_num}: {description} — {line.strip()}"
                            )
            if findings:
                return "SQL injection patterns detected:\n" + "\n".join(findings)
            return "No SQL injection patterns detected"

        @self.agent.tool
        async def run_tests(ctx: RunContext[AuditorDeps], test_path: str = "") -> str:
            """Independently re-run pytest to verify the fix works."""
            full_path = (
                f"{ctx.deps.app_root}/{test_path}" if test_path else ctx.deps.app_root
            )
            result = subprocess.run(
                ["pytest", full_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=ctx.deps.app_root,
            )
            return result.stdout + result.stderr

    async def run(self, proposal: ProposalPackage) -> AuditReport:
        deps = AuditorDeps(
            proposal=proposal,
            app_root="/Users/hunterbetz/workspace/sentinel",
        )
        prompt = (
            f"Review this proposal (iteration {proposal.iteration}):\n\n"
            f"Mechanic notes: {proposal.mechanic_notes}\n\n"
            f"Changed files: {[f.path for f in proposal.changed_files]}\n\n"
            f"Mechanic test results:\n{proposal.test_results}\n\n"
            f"Mechanic reports tests_passed={proposal.tests_passed}.\n\n"
            "Perform your independent audit now."
        )
        result = await self.agent.run(prompt, deps=deps)
        return result.output
