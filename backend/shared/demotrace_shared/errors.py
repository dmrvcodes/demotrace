"""Error codes a job can fail with, and the plain message the interface shows for each."""

from enum import StrEnum


class ErrorCode(StrEnum):
    VIDEO_TOO_LONG = "video_too_long"
    UNREADABLE_VIDEO = "unreadable_video"
    NO_VIDEO_STREAM = "no_video_stream"
    REQUEST_TOO_LARGE = "request_too_large"
    MODEL_REFUSED = "model_refused"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_REJECTED_REQUEST = "model_rejected_request"
    MODEL_INVALID_OUTPUT = "model_invalid_output"
    STORAGE_ERROR = "storage_error"
    INTERNAL_ERROR = "internal_error"


_TRY_AGAIN = "The analysis could not be completed — please try again."

ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VIDEO_TOO_LONG: "The video is longer than 3 minutes. Trim it and try again.",
    ErrorCode.UNREADABLE_VIDEO: "The video file could not be read. Re-export it as an H.264 MP4 and try again.",
    ErrorCode.NO_VIDEO_STREAM: "The file has no video track.",
    ErrorCode.REQUEST_TOO_LARGE: "The video has too much visual content to analyze in one pass.",
    ErrorCode.MODEL_REFUSED: "The analysis could not be completed for this video.",
    ErrorCode.MODEL_UNAVAILABLE: _TRY_AGAIN,
    ErrorCode.MODEL_REJECTED_REQUEST: _TRY_AGAIN,
    ErrorCode.MODEL_INVALID_OUTPUT: _TRY_AGAIN,
    ErrorCode.STORAGE_ERROR: _TRY_AGAIN,
    ErrorCode.INTERNAL_ERROR: _TRY_AGAIN,
}
