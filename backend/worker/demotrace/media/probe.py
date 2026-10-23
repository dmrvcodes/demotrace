"""Read duration, streams and start times with ffprobe, and enforce the 3-minute limit."""

import json
from dataclasses import dataclass
from pathlib import Path

from demotrace_shared.errors import ErrorCode
from demotrace_shared.limits import DURATION_TOLERANCE_S, MAX_DURATION_S

from . import PROTOCOLS, MediaError, ffprobe_bin, run_tool

PROBE_TIMEOUT_S = 30


@dataclass(frozen=True)
class ProbeInfo:
    duration_s: float
    video_start_s: float
    audio_start_s: float | None
    width: int
    height: int
    video_codec: str
    has_audio: bool


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def probe(path: Path) -> ProbeInfo:
    """Probe the video and refuse it if it is unreadable, has no video track or is too long.

    The browser checks the length too, but that check can be bypassed, so this is the real guard.
    """
    result = run_tool(
        [ffprobe_bin(), *PROTOCOLS, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        cap_s=PROBE_TIMEOUT_S, what="ffprobe",
    )
    if result.returncode != 0:
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, result.stderr.strip()[:300])
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])

    video = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")
        ),
        None,
    )
    if video is None:
        raise MediaError(ErrorCode.NO_VIDEO_STREAM)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = _float(data.get("format", {}).get("duration")) or _float(video.get("duration"))
    if not duration:
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, "no duration")
    if duration > MAX_DURATION_S + DURATION_TOLERANCE_S:
        raise MediaError(ErrorCode.VIDEO_TOO_LONG, f"{duration:.1f}s")

    return ProbeInfo(
        duration_s=duration,
        video_start_s=_float(video.get("start_time")) or 0.0,
        audio_start_s=(_float(audio.get("start_time")) or 0.0) if audio else None,
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        video_codec=str(video.get("codec_name") or "unknown"),
        has_audio=audio is not None,
    )
