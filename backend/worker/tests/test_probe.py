import pytest

from demotrace.media import MediaError
from demotrace.media.probe import probe
from demotrace_shared.errors import ErrorCode


def test_reads_duration_size_and_streams(clips):
    info = probe(clips["moving"])
    assert info.duration_s == pytest.approx(6, abs=0.2)
    assert (info.width, info.height) == (640, 360)
    assert info.has_audio and info.audio_start_s is not None


def test_silent_video_has_no_audio(clips):
    info = probe(clips["silent"])
    assert not info.has_audio and info.audio_start_s is None


def test_refuses_video_longer_than_three_minutes(clips):
    with pytest.raises(MediaError) as err:
        probe(clips["too_long"])
    assert err.value.code == ErrorCode.VIDEO_TOO_LONG


def test_refuses_unreadable_file(clips):
    with pytest.raises(MediaError) as err:
        probe(clips["garbage"])
    assert err.value.code == ErrorCode.UNREADABLE_VIDEO


def test_refuses_file_without_video_track(clips):
    with pytest.raises(MediaError) as err:
        probe(clips["audio_only"])
    assert err.value.code == ErrorCode.NO_VIDEO_STREAM
