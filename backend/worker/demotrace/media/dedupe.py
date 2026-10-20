"""Choose which frames to keep: drop near-duplicates, then the least novel frames until the cap holds.

Each frame gets two signals: a perceptual hash (structure) and a small colour thumbnail (which
pixels changed). The hash alone misses colour-only changes — a red and a blue screen hash the same —
and a status turning green can be exactly the evidence a claim needs. A frame counts as a duplicate
only when both signals say so.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

PHASH_SIZE = 16  # 256-bit hash
NEAR_DUPLICATE_BITS = 4  # out of 256
THUMB_SIZE = (384, 216)
PIXEL_CHANGE_LEVEL = 24  # a pixel counts as changed when any channel moves by more than this
# 0.02% of the thumbnail, about 17 pixels: roughly a single changed digit on a 1024 px frame.
# Tuned by the eval, not by guesswork.
NEAR_DUPLICATE_CHANGE = 0.0002


@dataclass(frozen=True)
class Signature:
    phash: imagehash.ImageHash
    thumb: np.ndarray  # uint8, THUMB_SIZE, RGB


def signatures(paths: Sequence[Path]) -> list[Signature]:
    sigs = []
    for p in paths:
        with Image.open(p) as img:
            rgb = img.convert("RGB")
            sigs.append(Signature(
                phash=imagehash.phash(rgb, hash_size=PHASH_SIZE),
                thumb=np.asarray(rgb.resize(THUMB_SIZE, Image.Resampling.BILINEAR), dtype=np.uint8),
            ))
    return sigs


def changed_fraction(a: Signature, b: Signature) -> float:
    diff = np.abs(a.thumb.astype(np.int16) - b.thumb.astype(np.int16)).max(axis=2)
    return float((diff > PIXEL_CHANGE_LEVEL).mean())


def is_near_duplicate(a: Signature, b: Signature) -> bool:
    return (a.phash - b.phash) <= NEAR_DUPLICATE_BITS and changed_fraction(a, b) <= NEAR_DUPLICATE_CHANGE


def novelty(a: Signature, b: Signature) -> float:
    """How much the later frame adds over the earlier one; used to order drops under the cap."""
    return changed_fraction(a, b) + (a.phash - b.phash) / PHASH_SIZE**2


def removal_order(n: int, distance: Callable[[int, int], float],
                  keep: Sequence[int] | None = None) -> list[int]:
    """Indices in the order they should be dropped, least novel first.

    Novelty of a frame is its distance to the previous frame still kept. The first frame is never
    dropped. `keep` limits the run to a subset (still in time order).
    """
    kept = list(range(n)) if keep is None else list(keep)
    order: list[int] = []
    while len(kept) > 1:
        # Ties go to the later frame, so the earlier occurrence of a screen survives.
        pos = min(range(1, len(kept)), key=lambda i: (distance(kept[i - 1], kept[i]), -i))
        order.append(kept.pop(pos))
    return order


def select(n: int, distance: Callable[[int, int], float], duplicate: Callable[[int, int], bool],
           max_frames: int) -> list[int]:
    """Indices to keep, in time order: near-duplicates of the previous kept frame go first."""
    kept = [0] if n else []
    for i in range(1, n):
        if not duplicate(kept[-1], i):
            kept.append(i)
    if len(kept) <= max_frames:
        return kept
    drop = set(removal_order(n, distance, keep=kept)[: len(kept) - max_frames])
    return [i for i in kept if i not in drop]
