import os

import pytest
from PIL import Image

from demotrace.media import budget


@pytest.fixture
def noisy_frames(tmp_path):
    """Random noise compresses badly, so these frames are as heavy as JPEG frames get."""
    paths = []
    for i in range(8):
        img = Image.frombytes("RGB", (1024, 576), os.urandom(1024 * 576 * 3))
        path = tmp_path / f"cand_{i:05d}.jpg"
        img.save(path, "JPEG", quality=95)
        paths.append(path)
    return paths


def by_position(a, b):
    return abs(a - b)


def test_base64_length():
    assert [budget.b64_len(n) for n in (0, 1, 2, 3, 4)] == [0, 4, 4, 4, 8]


def test_fits_unchanged_when_under_budget(noisy_frames):
    result = budget.fit(noisy_frames, 10_000, by_position, budget=100 * 1024 * 1024)
    assert result.quality is None and result.dropped == 0
    assert result.images[0] == noisy_frames[0].read_bytes()


def test_lowers_quality_before_dropping_frames(noisy_frames):
    at_85 = [len(budget.encode_jpeg(p, 85)) for p in noisy_frames]
    limit = budget.estimate_request_bytes(at_85, 10_000) + 1
    result = budget.fit(noisy_frames, 10_000, by_position, budget=limit)
    assert result.quality == 85 and result.dropped == 0 and len(result.keep) == len(noisy_frames)
    assert result.request_bytes <= limit


def test_drops_frames_when_lowest_quality_is_not_enough(noisy_frames):
    one_frame = len(budget.encode_jpeg(noisy_frames[0], budget.QUALITY_STEPS[-1]))
    limit = budget.estimate_request_bytes([one_frame] * 3, 10_000)
    result = budget.fit(noisy_frames, 10_000, by_position, budget=limit)
    assert result.quality == budget.QUALITY_STEPS[-1]
    assert result.dropped > 0 and result.keep[0] == 0
    assert result.request_bytes <= limit
    assert len(result.images) == len(result.keep)
