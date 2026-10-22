"""Temporary offline analyzer used while Bedrock access is blocked.

It deliberately labels the response as a fixture. The production worker replaces this module
with the validated media + model pipeline without changing the HTTP contract.
"""

from .models import AnalysisResult, ClaimResult, Evidence
from .store import Job


def analyze(job: Job) -> AnalysisResult:
    claims: list[ClaimResult] = []
    for index, text in enumerate(job.claims, start=1):
        claim_id = f"C{index}"
        if index == 1:
            claims.append(
                ClaimResult(
                    claim_id=claim_id,
                    text=text,
                    status="shown",
                    explanation="Local fixture result: replace with a Bedrock-backed assessment before submission.",
                    evidence=[Evidence(ref_id="F001", kind="frame", t=0)],
                )
            )
        elif index == 2:
            claims.append(
                ClaimResult(
                    claim_id=claim_id,
                    text=text,
                    status="told_only",
                    explanation="Local fixture result: this is a promised claim, not verified screen evidence.",
                    evidence=[Evidence(ref_id="F002", kind="frame", t=1)],
                )
            )
        else:
            claims.append(
                ClaimResult(
                    claim_id=claim_id,
                    text=text,
                    status="missing",
                    explanation="Local fixture result: no evidence was returned for this claim.",
                    evidence=[],
                )
            )
    return AnalysisResult(duration_s=0, claims=claims)
