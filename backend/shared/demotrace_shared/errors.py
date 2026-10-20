"""Error codes a job can fail with, and the plain message the interface shows for each."""

from enum import StrEnum


class ErrorCode(StrEnum):
    VIDEO_TOO_LONG = "video_too_long"
    UNREADABLE_VIDEO = "unreadable_video"
    NO_VIDEO_STREAM = "no_video_stream"
    REQUEST_TOO_LARGE = "request_too_large"


ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VIDEO_TOO_LONG: "The video is longer than 3 minutes. Trim it and try again.",
    ErrorCode.UNREADABLE_VIDEO: "The video file could not be read. Re-export it as an H.264 MP4 and try again.",
    ErrorCode.NO_VIDEO_STREAM: "The file has no video track.",
    ErrorCode.REQUEST_TOO_LARGE: "The video has too much visual content to analyze in one pass.",
}
