"""Save a model answer so the eval, the tests and the interface can replay it without a paid call.

A fixture holds IDs, times, the claims and the answer. It never holds frames, the video or the
transcript text.
"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from demotrace_shared.media import PreparedMedia

from .client import ModelResult
from .prompt import EFFORT, ModelRequest, claim_ids

FIXTURE_KIND = "demotrace.model_answer"


def fixture_data(name: str, media: PreparedMedia, claims: Sequence[str], request: ModelRequest,
                 result: ModelResult) -> dict:
    return {
        "kind": FIXTURE_KIND,
        "version": 1,
        "name": name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": request.params["model"],
        "effort": EFFORT,
        "request_bytes": request.size_bytes,
        "duration_s": media.duration_s,
        "sampling_step_s": media.sampling_step_s,
        "frames": [{"id": f.id, "t": f.t} for f in media.frames],
        "segments": [{"id": s.id, "start": s.start, "end": s.end} for s in media.segments],
        "claims": [{"id": cid, "text": text} for cid, text in zip(claim_ids(claims), claims)],
        "stop_reason": result.stop_reason,
        "usage": result.usage,
        "request_id": result.request_id,
        "elapsed_s": result.elapsed_s,
        "answer": result.answer.model_dump(mode="json"),
    }


def write_fixture(directory: Path, name: str, media: PreparedMedia, claims: Sequence[str],
                  request: ModelRequest, result: ModelResult) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(fixture_data(name, media, claims, request, result), indent=2,
                               ensure_ascii=False) + "\n")
    return path
