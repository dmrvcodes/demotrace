"""HTTP contracts shared by the local frontend and the future cloud adapter."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from demotrace_shared.limits import MAX_CLAIMS, MIN_CLAIMS


class JobStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Evidence(BaseModel):
    ref_id: str
    kind: str = "frame"
    t: float = Field(ge=0)


class ClaimResult(BaseModel):
    claim_id: str
    text: str
    status: str
    explanation: str
    evidence: list[Evidence]


class AnalysisResult(BaseModel):
    schema_version: int = 1
    duration_s: float = Field(ge=0)
    claims: list[ClaimResult]


class CreateJobResponse(BaseModel):
    job_id: str
    job_token: str
    upload_url: str


class AnalyzeRequest(BaseModel):
    claims: list[str]

    @field_validator("claims")
    @classmethod
    def validate_claims(cls, claims: list[str]) -> list[str]:
        cleaned = [claim.strip() for claim in claims]
        if not MIN_CLAIMS <= len(cleaned) <= MAX_CLAIMS:
            raise ValueError(f"submit {MIN_CLAIMS} to {MAX_CLAIMS} claims")
        if any(not claim for claim in cleaned):
            raise ValueError("claims cannot be empty")
        return cleaned


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: AnalysisResult | None = None
    error_code: str | None = None
    error_message: str | None = None
