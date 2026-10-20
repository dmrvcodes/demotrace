import shutil
import subprocess
from types import SimpleNamespace

import pytest

from demotrace import cli
from demotrace.stt.transcribe import to_segments
from demotrace_shared.media import PreparedMedia

from .conftest import VCODEC, ffmpeg


def seg(start, end, text):
    return SimpleNamespace(start=start, end=end, text=text)


def test_segments_are_labelled_shifted_and_empty_ones_skipped():
    raw = [seg(0.0, 1.2, " Hello there."), seg(1.2, 1.5, "  "), seg(1.5, 3.0, "Click export.")]
    out = to_segments(raw, offset_s=0.25)
    assert [s.id for s in out] == ["S01", "S02"]
    assert (out[0].start, out[0].end, out[0].text) == (0.25, 1.45, "Hello there.")
    assert out[1].start == 1.75


def test_segments_never_start_before_zero():
    out = to_segments([seg(0.0, 0.5, "Hi.")], offset_s=-0.3)
    assert out[0].start == 0.0 and out[0].end == 0.2


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("say") is None, reason="needs macOS `say`")
def test_prepare_end_to_end_with_real_speech(tmp_path):
    """The slice's mechanical check: a test pattern with a spoken sentence goes through `prepare`."""
    speech = tmp_path / "speech.aiff"
    subprocess.run(["say", "-o", str(speech),
                    "This is a product demo. Click export and the report downloads as a file."], check=True)
    video = tmp_path / "spoken.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=25:duration=8", "-i", str(speech),
           "-c:v", VCODEC, "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(video))

    out = tmp_path / "out"
    assert cli.main(["prepare", str(video), "--out", str(out)]) == 0

    media = PreparedMedia.model_validate_json((out / "media.json").read_text())
    text = " ".join(s.text for s in media.segments).lower()
    assert "export" in text and "report" in text
    assert media.has_audio and media.frames and media.frames[0].t == 0.0
    assert max(f.width for f in media.frames) == 1024  # 1280x720 scaled down to 1024 wide
    assert all((out / "frames" / f.file).exists() for f in media.frames)
    assert media.segments[0].start < 2.0
