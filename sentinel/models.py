"""
Shared Pydantic models used across Mechanic and Auditor agents.
"""

from typing import List

from pydantic import BaseModel


class ChangedFile(BaseModel):
    path: str
    new_content: str


class ProposalPackage(BaseModel):
    changed_files: List[ChangedFile]
    test_results: str
    tests_passed: bool
    mechanic_notes: str
    iteration: int


class AuditReport(BaseModel):
    approved: bool
    findings: List[str]
    recommendation: str
