"""Command line for the local pipeline. Run it from the repository root.

    python -m demotrace.cli prepare VIDEO --out DIR
    python -m demotrace.cli smoke [--video VIDEO --claims CLAIMS.json]
"""

import argparse
import sys
from pathlib import Path

from demotrace_shared.errors import ERROR_MESSAGES
from demotrace_shared.limits import REQUEST_MAX_BYTES

from .llm import ModelError
from .media import MediaError
from .prepare import prepare
from .timefmt import mmss


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


def cmd_smoke(args: argparse.Namespace) -> int:
    from .llm.client import call_model, make_client
    from .llm.fixtures import write_fixture
    from .llm.prompt import build_request
    from .smoke import describe, load_claims, load_frames, small_case

    client = make_client()
    fixtures = Path(args.fixtures)
    cases = []
    if not args.skip_small:
        cases.append(("smoke-small", *small_case()))
    if args.video:
        if not args.claims:
            raise SystemExit("--claims is required with --video")
        video = Path(args.video)
        out_dir = Path(args.out) / video.stem
        media = prepare(video, out_dir)
        cases.append((args.name or video.stem, media, load_frames(out_dir, media), load_claims(Path(args.claims))))

    for name, media, images, claims in cases:
        request = build_request(media, images, claims)
        print(f"\n== {name}: {len(media.frames)} frames, {len(media.segments)} segments, {len(claims)} claims, "
              f"request {request.size_bytes / 2**20:.2f} MB")
        result = call_model(client, request)
        usage = result.usage
        print(f"OK  stop_reason={result.stop_reason}  input_tokens={usage.get('input_tokens')}  "
              f"output_tokens={usage.get('output_tokens')}  time={result.elapsed_s}s  request_id={result.request_id}")
        print("\n".join(describe(claims, result.answer)))
        print(f"Saved {write_fixture(fixtures, name, media, claims, request, result)}")
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

    s = sub.add_parser("smoke", help="check the direct Claude call, then a realistic one with --video")
    s.add_argument("--video", help="a real demo video for the realistic request")
    s.add_argument("--claims", help="JSON file with 3–5 claims for --video")
    s.add_argument("--name", help="fixture name for the realistic request (default: the video's file name)")
    s.add_argument("--out", default="out/smoke", help="where prepared frames go")
    s.add_argument("--fixtures", default="eval/fixtures", help="where answers are saved")
    s.add_argument("--skip-small", action="store_true", help="only run the realistic request")
    s.set_defaults(func=cmd_smoke)

    from . import awsguard
    awsguard.load_env()  # local, gitignored .env in the directory you run from
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (MediaError, ModelError) as err:
        detail = f" ({err.detail})" if err.detail else ""
        request_id = getattr(err, "request_id", None)
        print(f"error: {err.code}: {ERROR_MESSAGES.get(err.code, '')}{detail}"
              + (f" request_id={request_id}" if request_id else ""), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
