"""What the model returns for each claim. The server validates it before anyone sees it."""

from enum import StrEnum

from pydantic import BaseModel


class ClaimStatus(StrEnum):
    SHOWN = "shown"
    TOLD_ONLY = "told_only"
    MISSING = "missing"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelClaimAssessment(BaseModel):
    # Evidence and explanation come before the verdict, so the verdict follows from them.
    claim_id: str
    evidence_ids: list[str]
    explanation: str
    status: ClaimStatus
    # Kept for the eval only; never sent to the browser (prd.md > Results and evidence).
    confidence: Confidence


class ModelAnswer(BaseModel):
    claims: list[ModelClaimAssessment]
