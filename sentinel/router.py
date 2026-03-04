"""
Semantic cost router
"""

from typing import Dict


def assess_problem(context: Dict) -> str:
    """
    Returns a pydantic-ai model string based on problem complexity.

    Tiers:
      - claude-haiku-4-5:  medium complexity (5xx from third-party flake)
      - claude-sonnet-4-6: high complexity  (latency spike / memory leak)
    """
    error_type = context.get("error_type", "")

    if error_type == "LATENCY_SPIKE":
        # Memory leaks require deep code analysis → heavier model
        return "anthropic:claude-sonnet-4-6"

    if error_type == "5xx_SPIKE":
        # Third-party error handling → lighter model sufficient
        return "anthropic:claude-haiku-4-5-20251001"

    # Unknown error — default to sonnet to be safe
    return "anthropic:claude-sonnet-4-6"
