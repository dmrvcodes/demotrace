"""Check the model's answer against the job's own input, and build the result the browser gets.

The server checks references and format only; it does not prove the model right, which is why the
interface says "AI assessment" (`spec.md > Result validation`).
"""

from collections.abc import Sequence

from demotrace_shared.analysis import ClaimStatus, ModelAnswer
from demotrace_shared.errors import ErrorCode
from demotrace_shared.media import PreparedMedia

from .llm import ModelError

RESULT_SCHEMA_VERSION = 1


def _invalid(detail: str) -> ModelError:
    return ModelError(ErrorCode.MODEL_INVALID_OUTPUT, detail)


def assemble_result(media: PreparedMedia, answer: ModelAnswer, claims: Sequence[str]) -> dict:
    """Return `{"schema_version", "duration_s", "claims": [...]}`, or raise MODEL_INVALID_OUTPUT.

    Timestamps come from the job's own frames and segments, never from the model.
    """
    refs = {f.id: ("frame", f.t) for f in media.frames} | {s.id: ("speech", s.start) for s in media.segments}
    expected = [f"C{n}" for n in range(1, len(claims) + 1)]

    by_id: dict[str, object] = {}
    for item in answer.claims:
        if item.claim_id not in expected:
            raise _invalid(f"unknown claim id {item.claim_id}")
        if item.claim_id in by_id:
            raise _invalid(f"duplicate claim id {item.claim_id}")
        by_id[item.claim_id] = item
    if missing := [cid for cid in expected if cid not in by_id]:
        raise _invalid(f"no assessment for {', '.join(missing)}")

    results = []
    for cid, text in zip(expected, claims):
        item = by_id[cid]
        if unknown := [ref for ref in item.evidence_ids if ref not in refs]:
            raise _invalid(f"{cid} cites unknown ids {', '.join(unknown)}")
        if len(set(item.evidence_ids)) != len(item.evidence_ids):
            raise _invalid(f"{cid} cites the same id twice")
        evidence = [{"ref_id": ref, "kind": refs[ref][0], "t": refs[ref][1]} for ref in item.evidence_ids]
        kinds = {e["kind"] for e in evidence}
        if item.status == ClaimStatus.SHOWN and "frame" not in kinds:
            raise _invalid(f"{cid} is shown without a frame")
        if item.status == ClaimStatus.TOLD_ONLY and not evidence:
            raise _invalid(f"{cid} is told_only without evidence")
        if item.status == ClaimStatus.MISSING and evidence:
            raise _invalid(f"{cid} is missing but cites evidence")
        if not item.explanation.strip():
            raise _invalid(f"{cid} has no explanation")
        results.append({
            "claim_id": cid,
            "text": text,
            "status": item.status.value,
            "explanation": item.explanation.strip(),
            "evidence": sorted(evidence, key=lambda e: e["t"]),
        })

    return {"schema_version": RESULT_SCHEMA_VERSION, "duration_s": media.duration_s, "claims": results}


def confidences(answer: ModelAnswer) -> dict[str, str]:
    """Kept on the job for the eval only; never part of the browser result."""
    return {item.claim_id: item.confidence.value for item in answer.claims}
