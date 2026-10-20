"""What the media preparation step produces: labelled frames and speech segments."""

from pydantic import BaseModel, Field


class Frame(BaseModel):
    id: str = Field(pattern=r"^F\d{3}$")
    # Seconds on the video's own timeline: the frame's pts_time minus the stream's start_time.
    t: float = Field(ge=0)
    file: str
    width: int
    height: int
    bytes: int


class SpeechSegment(BaseModel):
    id: str = Field(pattern=r"^S\d{2,}$")
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str


class PreparedMedia(BaseModel):
    schema_version: int = 1
    duration_s: float
    has_audio: bool
    width: int
    height: int
    video_codec: str
    frames: list[Frame]
    segments: list[SpeechSegment]
    sampling_step_s: float
    candidates: int
    jpeg_quality: int | None = None
    dropped_for_size: int = 0
    estimated_request_bytes: int
    stt_model: str | None = None
