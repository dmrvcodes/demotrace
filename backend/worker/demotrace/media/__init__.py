"""Video probing, frame extraction, de-duplication and the request-size budget."""

import os


class MediaError(Exception):
    """A video the pipeline cannot use; `code` is one of `demotrace_shared.errors.ErrorCode`."""

    def __init__(self, code, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else str(code))
        self.code = code
        self.detail = detail


def ffmpeg_bin() -> str:
    return os.environ.get("DEMOTRACE_FFMPEG", "ffmpeg")


def ffprobe_bin() -> str:
    return os.environ.get("DEMOTRACE_FFPROBE", "ffprobe")
