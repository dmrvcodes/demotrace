import pytest
from PIL import Image

from demotrace.media import dedupe
from demotrace.media.frames import extract_candidates, frame_filter, parse_showinfo_times
from demotrace.media.probe import probe


def keep(cands):
    sigs = dedupe.signatures([c.path for c in cands])
    return dedupe.select(len(cands), lambda a, b: dedupe.novelty(sigs[a], sigs[b]),
                         lambda a, b: dedupe.is_near_duplicate(sigs[a], sigs[b]), 90)


def test_filter_never_upscales_and_keeps_aspect():
    vf = frame_filter()
    assert "min(1024,iw)" in vf and "min(1024,ih)" in vf
    assert "force_original_aspect_ratio=decrease" in vf


def test_parses_showinfo_lines_only():
    stderr = (
        "[Parsed_showinfo_2 @ 0x1] n:   0 pts:      0 pts_time:0       duration:512\n"
        "frame=    3 fps=0.0 q=3.0 size=N/A time=00:00:01.00\n"
        "[Parsed_showinfo_2 @ 0x1] n:   1 pts:  12800 pts_time:1.04    duration:512\n"
    )
    assert parse_showinfo_times(stderr) == [0.0, 1.04]


def test_about_one_frame_per_second(clips, tmp_path):
    cands = extract_candidates(clips["moving"], probe(clips["moving"]), tmp_path)
    times = [c.t for c in cands]
    assert times[0] == 0.0
    assert times == sorted(times)
    assert 6 <= len(cands) <= 9  # 1 per second over 6 s, plus the odd scene change
    assert all(b - a >= 0.03 for a, b in zip(times, times[1:]))


def test_frames_are_scaled_within_1024(clips, tmp_path):
    cands = extract_candidates(clips["moving"], probe(clips["moving"]), tmp_path)
    with Image.open(cands[0].path) as img:
        assert img.size == (640, 360)  # smaller than 1024: left as is


def test_times_start_at_zero_when_the_stream_does_not(clips, tmp_path):
    info = probe(clips["offset"])
    assert info.video_start_s > 0.5  # MPEG-TS starts around 1.4 s
    cands = extract_candidates(clips["offset"], info, tmp_path)
    assert cands[0].t == 0.0
    assert cands[-1].t < info.duration_s


def test_scene_change_is_caught_between_seconds(clips, tmp_path):
    cands = extract_candidates(clips["two_colors"], probe(clips["two_colors"]), tmp_path)
    assert any(c.t == pytest.approx(1.5, abs=0.05) for c in cands)


def test_static_video_collapses_to_one_frame(clips, tmp_path):
    cands = extract_candidates(clips["static"], probe(clips["static"]), tmp_path)
    assert len(cands) >= 7
    assert keep(cands) == [0]


def test_two_colors_keep_one_frame_per_screen(clips, tmp_path):
    cands = extract_candidates(clips["two_colors"], probe(clips["two_colors"]), tmp_path)
    assert [cands[i].t for i in keep(cands)] == [0.0, pytest.approx(1.5, abs=0.05)]
