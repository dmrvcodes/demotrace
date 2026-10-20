"""Keep the model request at or under 16 MB as sent: lower JPEG quality first, then drop frames."""

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from demotrace_shared.limits import REQUEST_MAX_BYTES

from .dedupe import removal_order

QUALITY_STEPS = (85, 75, 65, 55, 45)
# JSON around one image block and its "Frame F012 · 00:41.0" label.
PER_IMAGE_OVERHEAD_BYTES = 200


def b64_len(n: int) -> int:
    return 4 * ((n + 2) // 3)


def estimate_request_bytes(image_sizes: Sequence[int], text_bytes: int) -> int:
    return text_bytes + sum(b64_len(s) + PER_IMAGE_OVERHEAD_BYTES for s in image_sizes)


def encode_jpeg(src: Path, quality: int) -> bytes:
    with Image.open(src) as img:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
        return buf.getvalue()


@dataclass
class BudgetResult:
    keep: list[int]  # indices into the input, in time order
    images: list[bytes]  # encoded JPEG bytes for the kept frames
    quality: int | None  # None when the original files fit unchanged
    dropped: int
    request_bytes: int


def fit(sources: Sequence[Path], text_bytes: int, distance: Callable[[int, int], int],
        budget: int = REQUEST_MAX_BYTES) -> BudgetResult:
    originals = [p.read_bytes() for p in sources]
    keep = list(range(len(sources)))
    size = estimate_request_bytes([len(b) for b in originals], text_bytes)
    if size <= budget:
        return BudgetResult(keep, originals, None, 0, size)

    images = originals
    quality = None
    for quality in QUALITY_STEPS:
        images = [encode_jpeg(p, quality) for p in sources]
        size = estimate_request_bytes([len(b) for b in images], text_bytes)
        if size <= budget:
            return BudgetResult(keep, images, quality, 0, size)

    # Still too large at the lowest quality: drop the least novel frames, one at a time.
    dropped: set[int] = set()
    for idx in removal_order(len(sources), distance):
        dropped.add(idx)
        size = estimate_request_bytes([len(images[i]) for i in keep if i not in dropped], text_bytes)
        if size <= budget:
            break
    keep = [i for i in keep if i not in dropped]
    return BudgetResult(keep, [images[i] for i in keep], quality, len(dropped), size)
