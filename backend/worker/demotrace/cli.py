"""Command line for the local pipeline: `python -m demotrace.cli prepare VIDEO --out DIR`."""

import argparse
import sys
from pathlib import Path

from demotrace_shared.errors import ERROR_MESSAGES
from demotrace_shared.limits import REQUEST_MAX_BYTES

from .media import MediaError
from .prepare import prepare


def mmss(t: float) -> str:
    minutes, seconds = divmod(t, 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"


def cmd_prepare(args: argparse.Namespace) -> int:
    media = prepare(Path(args.video), Path(args.out), with_speech=not args.no_speech,
                    whisper_model=args.whisper_model)
    audio = "yes" if media.has_audio else "no"
    quality = "original" if media.jpeg_quality is None else str(media.jpeg_quality)
    print(f"Video:  {mmss(media.duration_s)}  {media.width}x{media.height} {media.video_codec}, audio: {audio}")
    print(f"Frames: {len(media.frames)} kept of {media.candidates} candidates "
          f"(JPEG quality: {quality}, dropped for size: {media.dropped_for_size})")
    print(f"Request estimate: {media.estimated_request_bytes / 2**20:.1f} MB of {REQUEST_MAX_BYTES / 2**20:.0f} MB")
    print(f"Speech: {len(media.segments)} segments" + (f" ({media.stt_model})" if media.stt_model else ""))
    print("  " + ", ".join(f"{f.id} {mmss(f.t)}" for f in media.frames[:12])
          + (" …" if len(media.frames) > 12 else ""))
    for seg in media.segments[:5]:
        print(f"  {seg.id} [{mmss(seg.start)}–{mmss(seg.end)}] {seg.text}")
    print(f"Wrote {Path(args.out) / 'media.json'} and {len(media.frames)} frames in {Path(args.out) / 'frames'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="demotrace")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="extract labelled frames and speech segments from a video")
    p.add_argument("video")
    p.add_argument("--out", required=True, help="output directory (frames/ and media.json)")
    p.add_argument("--no-speech", action="store_true", help="skip speech to text")
    p.add_argument("--whisper-model", default=None, help="model size or local path (default: small.en)")
    p.set_defaults(func=cmd_prepare)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MediaError as err:
        detail = f" ({err.detail})" if err.detail else ""
        print(f"error: {err.code}: {ERROR_MESSAGES.get(err.code, '')}{detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
