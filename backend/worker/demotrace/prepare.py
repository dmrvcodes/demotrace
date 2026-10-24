"""Turn a video into labelled frames and speech segments: the input of the model call."""

import json
import tempfile
from pathlib import Path

from PIL import Image

from demotrace_shared.errors import ErrorCode
from demotrace_shared.limits import MAX_FRAMES, REQUEST_MAX_BYTES
from demotrace_shared.media import Frame, PreparedMedia

from .media import MediaError, budget, dedupe
from .media.frames import candidate_step_s, extract_candidates
from .media.probe import probe
from .stages import StageTracker, stage_of
from .stt import transcribe as stt

# Room kept in the request for the instructions, the claims and the labels around the transcript.
PROMPT_RESERVE_BYTES = 32 * 1024


def prepare(video: Path, out_dir: Path, *, with_speech: bool = True,
            whisper_model: str | None = None, tracker: StageTracker | None = None) -> PreparedMedia:
    """Write `out_dir/frames/F001.jpg…` and `out_dir/media.json`, and return the same data.

    With a `tracker`, frame work is timed as the "prepare" stage and speech as "transcribe".
    """
    stage = stage_of(tracker)
    with stage("prepare"):
        return _prepare(video, out_dir, with_speech, whisper_model, stage)


def _prepare(video: Path, out_dir: Path, with_speech: bool, whisper_model: str | None, stage) -> PreparedMedia:
    info = probe(video)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("F*.jpg"):
        old.unlink()

    with tempfile.TemporaryDirectory(prefix="demotrace-") as tmp_name:
        tmp = Path(tmp_name)
        candidates = extract_candidates(video, info, tmp / "candidates")
        sigs = dedupe.signatures([c.path for c in candidates])
        chosen = dedupe.select(
            len(candidates),
            lambda a, b: dedupe.novelty(sigs[a], sigs[b]),
            lambda a, b: dedupe.is_near_duplicate(sigs[a], sigs[b]),
            MAX_FRAMES,
        )

        with stage("transcribe"):
            segments = stt.transcribe(video, info, tmp, name=whisper_model) if with_speech else []
        transcript_bytes = len(json.dumps([s.model_dump() for s in segments]).encode())

        fitted = budget.fit(
            [candidates[i].path for i in chosen],
            PROMPT_RESERVE_BYTES + transcript_bytes,
            lambda a, b: dedupe.novelty(sigs[chosen[a]], sigs[chosen[b]]),
        )
        if fitted.request_bytes > REQUEST_MAX_BYTES:
            raise MediaError(ErrorCode.REQUEST_TOO_LARGE, f"{fitted.request_bytes} bytes")

        frames: list[Frame] = []
        for n, (idx, data) in enumerate(zip(fitted.keep, fitted.images), start=1):
            frame_id = f"F{n:03d}"
            path = frames_dir / f"{frame_id}.jpg"
            path.write_bytes(data)
            with Image.open(path) as img:
                width, height = img.size
            frames.append(Frame(id=frame_id, t=candidates[chosen[idx]].t, file=path.name,
                                width=width, height=height, bytes=len(data)))

    media = PreparedMedia(
        duration_s=round(info.duration_s, 3),
        has_audio=info.has_audio,
        width=info.width,
        height=info.height,
        video_codec=info.video_codec,
        frames=frames,
        segments=segments,
        sampling_step_s=candidate_step_s(info.duration_s),
        candidates=len(candidates),
        jpeg_quality=fitted.quality,
        dropped_for_size=fitted.dropped,
        estimated_request_bytes=fitted.request_bytes,
        stt_model=stt.model_name(whisper_model) if with_speech and info.has_audio else None,
    )
    (out_dir / "media.json").write_text(media.model_dump_json(indent=2))
    return media
