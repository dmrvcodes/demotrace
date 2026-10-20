"""The Bedrock smoke test: one small request, then one realistic request built from a real video.

Together they check the five things from `spec.md > How We Verify`: the model answers,
`messages.parse` with structured output works, effort `high` is accepted, the request size goes
through, and the token quota holds.
"""

import io
import json
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from demotrace_shared.limits import MAX_CLAIMS, MIN_CLAIMS
from demotrace_shared.media import Frame, PreparedMedia, SpeechSegment

SMALL_CLAIMS = [
    "Clicking Export downloads the report as a CSV file.",
    "The report can be shared with a link.",
]


def small_case() -> tuple[PreparedMedia, list[bytes], list[str]]:
    """One synthetic frame, one speech segment, two claims: the cheapest request that exercises it all."""
    img = Image.new("RGB", (1024, 576), (9, 9, 11))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((262, 208, 762, 368), radius=12, outline=(16, 185, 129), width=3, fill=(24, 24, 27))
    draw.text((300, 236), "Export complete", fill=(244, 244, 245), font=ImageFont.load_default(size=40))
    draw.text((300, 300), "q3-report.csv downloaded", fill=(16, 185, 129), font=ImageFont.load_default(size=30))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    data = buf.getvalue()

    media = PreparedMedia(
        duration_s=3.0, has_audio=True, width=1024, height=576, video_codec="synthetic",
        frames=[Frame(id="F001", t=0.0, file="F001.jpg", width=1024, height=576, bytes=len(data))],
        segments=[SpeechSegment(id="S01", start=0.0, end=2.5, text="Now I click export and the report downloads.")],
        sampling_step_s=1.0, candidates=1, estimated_request_bytes=0,
    )
    return media, [data], list(SMALL_CLAIMS)


def load_claims(path: Path, *, minimum: int = MIN_CLAIMS, maximum: int = MAX_CLAIMS) -> list[str]:
    """A JSON list of strings, or `{"claims": [...]}`."""
    data = json.loads(path.read_text())
    claims = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(claims, list) or not all(isinstance(c, str) for c in claims):
        raise ValueError(f"{path}: expected a list of claim strings")
    claims = [c.strip() for c in claims if c.strip()]
    if not minimum <= len(claims) <= maximum:
        raise ValueError(f"{path}: {len(claims)} claims, expected {minimum}–{maximum}")
    return claims


def load_frames(out_dir: Path, media: PreparedMedia) -> list[bytes]:
    return [(out_dir / "frames" / f.file).read_bytes() for f in media.frames]


def describe(claims: Sequence[str], answer) -> list[str]:
    by_id = {a.claim_id: a for a in answer.claims}
    lines = []
    for i, text in enumerate(claims, start=1):
        a = by_id.get(f"C{i}")
        if a is None:
            lines.append(f"  C{i} (no assessment)  {text}")
            continue
        evidence = ", ".join(a.evidence_ids) or "-"
        lines.append(f"  C{i} {a.status.value.upper()} ({a.confidence.value}) [{evidence}]  {text}")
        lines.append(f"      {a.explanation}")
    return lines
