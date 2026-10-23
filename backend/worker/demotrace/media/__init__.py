"""Video probing, frame extraction, de-duplication and the request-size budget.

Every ffmpeg/ffprobe run goes through `run_tool`: a timeout derived from the time the Lambda has
left (so one hanging file cannot hold a worker for 15 minutes), local files only, and a minimal
environment so the tools never see the API key or AWS credentials.
"""

import os
import subprocess
import time

from demotrace_shared.errors import ErrorCode

# Room left after a tool times out, to write FAILED and clean up.
RESERVE_S = 30.0
MIN_TIMEOUT_S = 1.0
# ffmpeg may only read local files and pipes: no network fetches from inside a crafted container.
PROTOCOLS = ["-protocol_whitelist", "file,pipe"]

_deadline: float | None = None  # time.monotonic() value when the Lambda runs out of time


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


def set_deadline(seconds_left: float | None) -> None:
    """Called by the Lambda handler with the invocation's remaining time; None means no deadline."""
    global _deadline
    _deadline = None if seconds_left is None else time.monotonic() + seconds_left


def tool_timeout(cap_s: float) -> float:
    if _deadline is None:
        return cap_s
    return max(MIN_TIMEOUT_S, min(cap_s, _deadline - time.monotonic() - RESERVE_S))


def tool_env() -> dict[str, str]:
    return {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/tmp")}


def run_tool(args: list[str], *, cap_s: float, what: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=tool_timeout(cap_s), env=tool_env())
    except subprocess.TimeoutExpired as err:
        raise MediaError(ErrorCode.UNREADABLE_VIDEO, f"{what} timed out") from err
