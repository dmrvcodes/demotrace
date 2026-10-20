"""Small test clips generated with ffmpeg, so no real video is ever needed in the repository."""

import subprocess
from pathlib import Path

import pytest


def _encoders() -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout


VCODEC = "libx264" if " libx264 " in _encoders() else "mpeg4"


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def make_clip(path: Path, *, source: str = "testsrc2=size=640x360:rate=25", duration: float = 3,
              audio: bool = True) -> Path:
    args = ["-f", "lavfi", "-i", f"{source}:duration={duration}"]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
    args += ["-c:v", VCODEC, "-pix_fmt", "yuv420p"]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    ffmpeg(*args, str(path))
    return path


@pytest.fixture(scope="session")
def clips(tmp_path_factory) -> dict[str, Path]:
    d = tmp_path_factory.mktemp("clips")
    two_colors = d / "two_colors.mp4"
    ffmpeg(
        "-f", "lavfi", "-i", "color=c=red:size=320x240:rate=25:duration=1.5",
        "-f", "lavfi", "-i", "color=c=blue:size=320x240:rate=25:duration=1.5",
        "-filter_complex", "[0][1]concat=n=2:v=1:a=0",
        "-c:v", VCODEC, "-pix_fmt", "yuv420p", str(two_colors),
    )
    garbage = d / "garbage.mp4"
    garbage.write_bytes(b"this is not a video")
    audio_only = d / "audio_only.m4a"
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:a", "aac", str(audio_only))
    return {
        "moving": make_clip(d / "moving.mp4", duration=6),
        "silent": make_clip(d / "silent.mp4", duration=3, audio=False),
        "static": make_clip(d / "static.mp4", source="color=c=gray:size=640x360:rate=25", duration=8, audio=False),
        # MPEG-TS streams start at a non-zero time (about 1.4 s), which exercises the start_time offset.
        "offset": make_clip(d / "offset.ts", duration=4, audio=False),
        "too_long": make_clip(d / "too_long.mp4", source="color=c=black:size=32x32:rate=1", duration=182,
                              audio=False),
        "two_colors": two_colors,
        "garbage": garbage,
        "audio_only": audio_only,
    }
