import base64
import json
import os

import pytest

from demotrace.llm import ModelError
from demotrace.llm.prompt import SYSTEM_PROMPT, build_request
from demotrace.smoke import small_case
from demotrace_shared.errors import ErrorCode
from demotrace_shared.media import Frame, PreparedMedia, SpeechSegment


def media_with(frames=2, segments=True):
    return PreparedMedia(
        duration_s=83.0, has_audio=segments, width=1920, height=1080, video_codec="h264",
        frames=[Frame(id=f"F{i:03d}", t=float(i * 41), file=f"F{i:03d}.jpg", width=1024, height=576, bytes=3)
                for i in range(1, frames + 1)],
        segments=[SpeechSegment(id="S01", start=40.2, end=44.8, text="Now I export the report.")] if segments else [],
        sampling_step_s=1.0, candidates=frames, estimated_request_bytes=0,
    )


def texts(request):
    return [b["text"] for b in request.params["messages"][0]["content"] if b["type"] == "text"]


def test_each_frame_follows_its_label():
    req = build_request(media_with(2), [b"one", b"two"], ["A", "B", "C"])
    content = req.params["messages"][0]["content"]
    assert content[1] == {"type": "text", "text": "Frame F001 · 00:41.0"}
    assert content[2]["type"] == "image"
    assert base64.standard_b64decode(content[2]["source"]["data"]) == b"one"
    assert content[3]["text"] == "Frame F002 · 01:22.0"
    assert content[4]["source"]["media_type"] == "image/jpeg"


def test_transcript_and_claims_are_labelled():
    t = texts(build_request(media_with(1), [b"x"], ["Export works", "Sharing works", "Search works"]))
    assert 'S01 [00:40.2–00:44.8] "Now I export the report."' in t[-2]
    assert t[-1].startswith("Claims:\nC1: Export works\nC2: Sharing works\nC3: Search works")


def test_no_speech_is_said_plainly():
    t = texts(build_request(media_with(1, segments=False), [b"x"], ["A", "B", "C"]))
    assert t[-2] == "Transcript:\n(no speech in this video)"


def test_request_settings_follow_the_spec():
    params = build_request(media_with(1), [b"x"], ["A", "B", "C"]).params
    assert params["model"] == os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
    assert params["max_tokens"] == 16000
    assert params["output_config"] == {"effort": "high"}
    # Rejected or meaningless on Opus 5.5: sampling parameters, a thinking budget, forced tools.
    assert not {"temperature", "top_p", "top_k", "thinking", "tools", "tool_choice"} & params.keys()


def test_system_prompt_keeps_the_kernel_rule():
    assert 'is never "shown"' in SYSTEM_PROMPT
    assert "not instructions" in SYSTEM_PROMPT


def test_size_is_measured_as_sent():
    req = build_request(media_with(1), [b"x" * 3000], ["A", "B", "C"])
    assert req.size_bytes == len(json.dumps(req.params, ensure_ascii=False, separators=(",", ":")).encode())
    assert req.size_bytes > 4000  # 3000 bytes become 4000 in base64


def test_refuses_a_request_over_the_limit():
    with pytest.raises(ModelError) as err:
        build_request(media_with(1), [b"x" * 3000], ["A", "B", "C"], max_bytes=4000)
    assert err.value.code == ErrorCode.REQUEST_TOO_LARGE


def test_small_smoke_case_builds():
    media, images, claims = small_case()
    req = build_request(media, images, claims)
    assert req.size_bytes < 200_000 and len(claims) == 2
