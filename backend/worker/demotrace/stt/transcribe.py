"""Speech to text with faster-whisper; segment times are moved onto the video's own timeline."""

import os
import subprocess
import wave
from pathlib import Path

import numpy as np

from demotrace_shared.errors import ErrorCode
from demotrace_shared.media import SpeechSegment

from ..media import MediaError, ffmpeg_bin
from ..media.probe import ProbeInfo

# Locally a model size is downloaded once into the Hugging Face cache; in Lambda this is a path
# under /opt/models baked into the image. The size is chosen by measurement, not in advance.
DEFAULT_MODEL = "small.en"

_models: dict[str, object] = {}


def model_name(override: str | None = None) -> str:
    return override or os.environ.get("DEMOTRACE_WHISPER_MODEL", DEFAULT_MODEL)


def load_model(name: str):
    from faster_whisper import WhisperModel

    if name not in _models:
        _models[name] = WhisperModel(
            name,
            device="cpu",
            compute_type="int8",
            cpu_threads=int(os.environ.get("DEMOTRACE_WHISPER_THREADS", "0")),
        )
    return _models[name]


def extract_audio(video: Path, wav: Path) -> None:
    result = subprocess.run(
        [
            ffmpeg_bin(), "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(video), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            str(wav),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, "audio: " + result.stderr.strip()[-300:])


def read_wav(wav: Path) -> np.ndarray:
    """16 kHz mono PCM as float32 in [-1, 1].

    Handing whisper an array instead of a path skips its own PyAV decoding, which breaks across PyAV
    releases (faster-whisper 1.2.1 passes `metadata_errors`, which PyAV 19 no longer accepts).
    """
    with wave.open(str(wav), "rb") as w:
        pcm = w.readframes(w.getnframes())
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


def to_segments(raw, offset_s: float) -> list[SpeechSegment]:
    """Label segments S01, S02, … and shift them by `offset_s`; empty segments are skipped."""
    out: list[SpeechSegment] = []
    for seg in raw:
        text = seg.text.strip()
        if not text:
            continue
        start = max(0.0, seg.start + offset_s)
        end = max(start, seg.end + offset_s)
        out.append(SpeechSegment(id=f"S{len(out) + 1:02d}", start=round(start, 2), end=round(end, 2), text=text))
    return out


def transcribe(video: Path, info: ProbeInfo, workdir: Path, *, model=None,
               name: str | None = None) -> list[SpeechSegment]:
    """No audio track means no segments: a claim shown only on a slide can still be Told only."""
    if not info.has_audio:
        return []
    wav = workdir / "audio.wav"
    extract_audio(video, wav)
    model = model or load_model(model_name(name))
    raw, _ = model.transcribe(read_wav(wav), language="en", vad_filter=True, beam_size=5)
    # The extracted audio starts at the audio stream's first sample; frames are measured from the
    # video stream's start, so shift speech by the difference between the two start times.
    return to_segments(raw, (info.audio_start_s or 0.0) - info.video_start_s)
