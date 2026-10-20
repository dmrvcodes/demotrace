import random

from demotrace.media import dedupe


def test_drops_near_duplicates_of_the_previous_kept_frame():
    # Frame 1 is a near copy of frame 0; frame 3 returns to a screen seen earlier but is kept,
    # because only the previous kept frame counts.
    values = [0, 2, 100, 0, 200, 300]
    dist = lambda a, b: abs(values[a] - values[b])
    dup = lambda a, b: dist(a, b) <= 4
    assert dedupe.select(len(values), dist, dup, max_frames=90) == [0, 2, 3, 4, 5]


def test_cap_keeps_first_frame_and_the_big_changes():
    rng = random.Random(7)
    values, big_changes = [], set()
    v = 0
    for i in range(200):
        jump = 1000 if i % 25 == 0 and i else rng.randint(5, 60)
        if jump == 1000:
            big_changes.add(i)
        v += jump
        values.append(v)
    dist = lambda a, b: abs(values[a] - values[b])

    kept = dedupe.select(len(values), dist, lambda a, b: dist(a, b) <= 4, max_frames=90)
    assert len(kept) == 90
    assert kept[0] == 0
    assert kept == sorted(kept)
    assert big_changes <= set(kept)


def test_removal_order_never_drops_the_first_frame():
    values = [0, 1, 2, 3]
    order = dedupe.removal_order(len(values), lambda a, b: abs(values[a] - values[b]))
    assert 0 not in order and sorted(order) == [1, 2, 3]


def test_colour_only_change_is_not_a_duplicate(tmp_path):
    """Same layout, different colour: the perceptual hash matches, the pixel check does not."""
    from PIL import Image

    red, green = tmp_path / "red.jpg", tmp_path / "green.jpg"
    Image.new("RGB", (640, 360), (200, 40, 40)).save(red)
    Image.new("RGB", (640, 360), (40, 160, 40)).save(green)
    a, b = dedupe.signatures([red, green])
    assert a.phash - b.phash <= dedupe.NEAR_DUPLICATE_BITS
    assert not dedupe.is_near_duplicate(a, b)


def test_small_text_appearing_is_not_a_duplicate(tmp_path):
    """A short label showing up on an otherwise identical screen keeps the frame."""
    from PIL import Image, ImageDraw

    before, after = tmp_path / "before.jpg", tmp_path / "after.jpg"
    base = Image.new("RGB", (1024, 576), (24, 24, 27))
    base.save(before, quality=90)
    shown = base.copy()
    ImageDraw.Draw(shown).text((900, 540), "Saved", fill=(16, 185, 129))
    shown.save(after, quality=90)
    a, b = dedupe.signatures([before, after])
    assert not dedupe.is_near_duplicate(a, b)
