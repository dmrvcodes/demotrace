import pytest

from demotrace.llm import ModelError
from demotrace.validate import assemble_result, confidences
from demotrace_shared.analysis import ModelAnswer
from demotrace_shared.errors import ErrorCode
from demotrace_shared.media import Frame, PreparedMedia, SpeechSegment

MEDIA = PreparedMedia(
    duration_s=60.0, has_audio=True, width=1280, height=720, video_codec="h264",
    frames=[Frame(id="F001", t=0.0, file="F001.jpg", width=1024, height=576, bytes=1),
            Frame(id="F002", t=41.0, file="F002.jpg", width=1024, height=576, bytes=1)],
    segments=[SpeechSegment(id="S01", start=3.2, end=6.0, text="We will add sharing soon.")],
    sampling_step_s=1.0, candidates=2, estimated_request_bytes=0,
)
CLAIMS = ["Export downloads a CSV.", "Reports can be shared.", "There is a dark mode."]


def assessment(cid, status, ids=(), conf="high", explanation="Because."):
    return {"claim_id": cid, "evidence_ids": list(ids), "explanation": explanation, "status": status,
            "confidence": conf}


def answer(*items):
    return ModelAnswer.model_validate({"claims": list(items)})


GOOD = answer(
    assessment("C1", "shown", ["F002", "F001"]),
    assessment("C2", "told_only", ["S01"], conf="medium"),
    assessment("C3", "missing"),
)


def invalid(ans, claims=CLAIMS):
    with pytest.raises(ModelError) as err:
        assemble_result(MEDIA, ans, claims)
    assert err.value.code == ErrorCode.MODEL_INVALID_OUTPUT
    return err.value.detail


def test_builds_the_browser_result_with_server_timestamps():
    result = assemble_result(MEDIA, GOOD, CLAIMS)
    assert result["schema_version"] == 1 and result["duration_s"] == 60.0
    c1, c2, c3 = result["claims"]
    assert c1["text"] == CLAIMS[0] and c1["status"] == "shown"
    assert [e["t"] for e in c1["evidence"]] == [0.0, 41.0]  # sorted by time, times from our frames
    assert c2["evidence"] == [{"ref_id": "S01", "kind": "speech", "t": 3.2}]
    assert c3["evidence"] == []
    assert all("confidence" not in c for c in result["claims"])


def test_confidence_is_kept_apart():
    assert confidences(GOOD) == {"C1": "high", "C2": "medium", "C3": "high"}


def test_missing_claim_is_invalid_not_a_crash():
    assert "C3" in invalid(answer(assessment("C1", "missing"), assessment("C2", "missing")))


def test_unknown_and_duplicate_claim_ids():
    assert "C9" in invalid(answer(*GOOD.model_dump()["claims"], assessment("C9", "missing")))
    assert "duplicate" in invalid(answer(assessment("C1", "missing"), assessment("C1", "missing"),
                                         assessment("C2", "missing"), assessment("C3", "missing")))


def test_unknown_evidence_id():
    assert "F404" in invalid(answer(assessment("C1", "shown", ["F404"]), assessment("C2", "missing"),
                                    assessment("C3", "missing")))


def test_shown_needs_a_frame():
    assert "without a frame" in invalid(answer(assessment("C1", "shown", ["S01"]), assessment("C2", "missing"),
                                               assessment("C3", "missing")))


def test_told_only_needs_evidence_and_missing_needs_none():
    assert "told_only" in invalid(answer(assessment("C1", "told_only"), assessment("C2", "missing"),
                                         assessment("C3", "missing")))
    assert "missing but cites" in invalid(answer(assessment("C1", "missing", ["F001"]),
                                                 assessment("C2", "missing"), assessment("C3", "missing")))


def test_empty_explanation_is_invalid():
    assert "explanation" in invalid(answer(assessment("C1", "missing", explanation="  "),
                                           assessment("C2", "missing"), assessment("C3", "missing")))
