import subprocess
from pathlib import Path

import pytest

from demotrace import media
from demotrace.media import MediaError, frames, probe
from demotrace.media.probe import ProbeInfo
from demotrace.stt import transcribe
from demotrace_shared.errors import ErrorCode

INFO = ProbeInfo(duration_s=10, video_start_s=0, audio_start_s=0, width=640, height=360, video_codec="h264",
                 has_audio=True)


@pytest.fixture(autouse=True)
def no_deadline():
    media.set_deadline(None)
    yield
    media.set_deadline(None)


def test_a_hanging_tool_becomes_unreadable_video():
    with pytest.raises(MediaError) as err:
        media.run_tool(["sleep", "5"], cap_s=0.3, what="test tool")
    assert err.value.code == ErrorCode.UNREADABLE_VIDEO and "timed out" in err.value.detail


def test_tools_never_see_secrets(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-not-leak")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-leak")
    out = media.run_tool(["env"], cap_s=5, what="env").stdout
    assert "should-not-leak" not in out
    assert set(line.split("=", 1)[0] for line in out.splitlines() if "=" in line) <= {"PATH", "HOME", "PWD", "SHLVL", "_"}


def test_timeout_follows_the_lambda_deadline():
    assert media.tool_timeout(180) == 180
    media.set_deadline(120)
    assert 89 <= media.tool_timeout(180) <= 90  # 120 s left minus the 30 s reserve
    media.set_deadline(10)
    assert media.tool_timeout(180) == media.MIN_TIMEOUT_S


def recorded(monkeypatch, module):
    calls = []

    def fake_run(args, *, cap_s, what):
        calls.append((args, cap_s))
        return subprocess.CompletedProcess(args, 1, "", "boom")

    monkeypatch.setattr(module, "run_tool", fake_run)
    return calls


def test_ffprobe_reads_local_files_only(monkeypatch):
    calls = recorded(monkeypatch, probe)
    with pytest.raises(MediaError):
        probe.probe(Path("in.mp4"))
    args, cap = calls[0]
    assert args[1:3] == ["-protocol_whitelist", "file,pipe"] and cap == 30


def test_frame_and_audio_extraction_stop_at_the_length_limit(monkeypatch, tmp_path):
    calls = recorded(monkeypatch, frames)
    with pytest.raises(MediaError):
        frames.extract_candidates(Path("in.mp4"), INFO, tmp_path)
    args, cap = calls[0]
    assert "-protocol_whitelist" in args and args[args.index("-t") + 1] == "180.5" and cap == 180

    calls = recorded(monkeypatch, transcribe)
    with pytest.raises(MediaError):
        transcribe.extract_audio(Path("in.mp4"), tmp_path / "a.wav")
    args, cap = calls[0]
    assert "-protocol_whitelist" in args and args[args.index("-t") + 1] == "180.5" and cap == 120
