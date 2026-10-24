"""Extract candidate frames with ffmpeg: one per second plus scene changes, scaled to 1024 px."""

import re
from dataclasses import dataclass
from pathlib import Path

from demotrace_shared.errors import ErrorCode
from demotrace_shared.limits import DURATION_TOLERANCE_S, FRAME_MAX_SIDE, FRAME_SAMPLING_STEP_S, MAX_DURATION_S

from . import PROTOCOLS, MediaError, ffmpeg_bin, run_tool
from .probe import ProbeInfo

SCENE_THRESHOLD = 0.3
FRAMES_TIMEOUT_S = 180
MAX_READ_S = MAX_DURATION_S + DURATION_TOLERANCE_S  # 180.5
CANDIDATE_JPEG_QSCALE = 3  # ffmpeg's -q:v scale, 2 (best) to 31 (worst)
TRANSIENT_UI_MAX_DURATION_S = 90.0
TRANSIENT_UI_STEP_S = 0.5

_PTS_TIME = re.compile(r"\bpts_time:\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)")


@dataclass(frozen=True)
class Candidate:
    path: Path
    t: float  # seconds on the video's own timeline


def frame_filter(step_s: float = FRAME_SAMPLING_STEP_S, max_side: int = FRAME_MAX_SIDE) -> str:
    """The ffmpeg filter chain. Never upscales; keeps the aspect ratio."""
    scale = f"scale='min({max_side},iw)':'min({max_side},ih)':force_original_aspect_ratio=decrease"
    # First frame, then a frame whenever `step_s` has passed since the last pick, plus scene changes.
    select = (
        f"select='gt(eq(n,0)+gte(t-prev_selected_t,{step_s})+gt(scene,{SCENE_THRESHOLD}),0)'"
    )
    return ",".join([scale, select, "showinfo"])


def candidate_step_s(duration_s: float) -> float:
    """Sample short clips twice per second so short-lived UI feedback is observable.

    The frame budget still caps what reaches the model.  Long videos retain the documented
    one-frame-per-second cadence, while a <= 90 s proof-of-concept clip can capture a toast
    that appears wholly between two one-second samples.
    """
    return TRANSIENT_UI_STEP_S if duration_s <= TRANSIENT_UI_MAX_DURATION_S else FRAME_SAMPLING_STEP_S


def parse_showinfo_times(stderr: str) -> list[float]:
    return [
        float(match.group(1))
        for line in stderr.splitlines()
        if "Parsed_showinfo" in line and (match := _PTS_TIME.search(line))
    ]


def extract_candidates(video: Path, info: ProbeInfo, out_dir: Path, *, step_s: float | None = None) -> list[Candidate]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sampling_step_s = candidate_step_s(info.duration_s) if step_s is None else step_s
    result = run_tool(
        [
            ffmpeg_bin(), "-hide_banner", "-nostdin", "-loglevel", "info", *PROTOCOLS,
            "-i", str(video),
            "-t", str(MAX_READ_S),  # never read past the length limit, whatever the container claims
            "-map", "0:v:0",
            "-vf", frame_filter(sampling_step_s),
            "-fps_mode", "vfr",
            "-q:v", str(CANDIDATE_JPEG_QSCALE),
            str(out_dir / "cand_%05d.jpg"),
        ],
        cap_s=FRAMES_TIMEOUT_S, what="frame extraction",
    )
    if result.returncode != 0:
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, result.stderr.strip()[-300:])

    files = sorted(out_dir.glob("cand_*.jpg"))
    times = parse_showinfo_times(result.stderr)
    if not files or len(files) != len(times):
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, f"{len(files)} frames, {len(times)} timestamps")

    # The plan's rule: a frame's time is its pts_time minus the video stream's start_time.
    return [
        Candidate(path=f, t=round(max(0.0, pts - info.video_start_s), 3))
        for f, pts in zip(files, times)
    ]
