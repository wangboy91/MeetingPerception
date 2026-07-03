from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AudioFrame(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    track: Literal["mic", "system"]
    timestamp_ms: int = Field(alias="timestampMs")
    sample_rate: Literal[16000] = Field(alias="sampleRate")
    channels: Literal[1]
    format: Literal["pcm_s16le"]
    seq: int
    rms: float
    data: str
