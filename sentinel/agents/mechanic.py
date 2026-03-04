"""
Identifies the problem and implements the fix.
Should use a heavier model for complex reasoning.
"""

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Optional

from pydantic_ai import Agent, RunContext

from sentinel.models import ProposalPackage


@dataclass
class MechanicDeps:
    app_root: str
    error_context: Dict
    audit_feedback: Optional[str] = None
    written_files: Dict[str, str] = field(default_factory=dict)


class Mechanic:

    def __init__(self, model: str = "anthropic:claude-sonnet-4-6"):
        self.agent = Agent(
            model,
            deps_type=MechanicDeps,
            output_type=ProposalPackage,
            system_prompt=(
                "You are a Mechanic. Your job is to fix the problems that are being presented to you. "
                "Your approach should be to:\n"
                "1. Explore the project structure with list_directory\n"
                "2. Read the relevant source files with read_file\n"
                "3. Write a unit test that replicates the error using write_file\n"
                "4. Implement the actual fix using write_file\n"
                "5. Run the tests with run_tests to verify the fix works\n"
                "The app root is available via deps.app_root.\n\n"
                "Return a ProposalPackage with:\n"
                "- changed_files: list of every file you wrote (path + new_content)\n"
                "- test_results: the full pytest output\n"
                "- tests_passed: true only if pytest exited 0\n"
                "- mechanic_notes: brief explanation of what you changed and why\n"
                "- iteration: the current iteration number"
            ),
        )
        self._register_tools()

    def _register_tools(self) -> None:
        """Attach tools to the internal agent."""

        @self.agent.tool
        async def read_file(ctx: RunContext[MechanicDeps], path: str) -> str:
            """Read a source file relative to app_root."""
            full_path = f"{ctx.deps.app_root}/{path}"
            with open(full_path, "r") as f:
                return f.read()

        @self.agent.tool
        async def list_directory(ctx: RunContext[MechanicDeps], path: str = "") -> str:
            """List directory contents relative to app_root."""
            full_path = f"{ctx.deps.app_root}/{path}" if path else ctx.deps.app_root
            entries = os.listdir(full_path)
            return "\n".join(sorted(entries))

        @self.agent.tool
        async def write_file(
            ctx: RunContext[MechanicDeps], path: str, content: str
        ) -> str:
            """Write content to a file relative to app_root and track it."""
            full_path = f"{ctx.deps.app_root}/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            ctx.deps.written_files[path] = content
            return f"Written {full_path}"

        @self.agent.tool
        async def run_tests(ctx: RunContext[MechanicDeps], test_path: str = "") -> str:
            """Run pytest on the given path (relative to app_root) and return output."""
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

    async def run(
        self,
        error_context: Dict,
        audit_feedback: Optional[str] = None,
        iteration: int = 1,
    ) -> ProposalPackage:
        deps = MechanicDeps(
            app_root="/Users/hunterbetz/workspace/sentinel",
            error_context=error_context,
            audit_feedback=audit_feedback,
        )
        prompt = f"Fix the following error: {error_context}"
        if audit_feedback:
            prompt += (
                f"\n\nIteration {iteration}. Auditor rejected:\n{audit_feedback}\n"
                "Address all findings."
            )
        result = await self.agent.run(prompt, deps=deps)
        return result.output
