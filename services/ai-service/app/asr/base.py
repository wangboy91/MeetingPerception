from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel


class SpeechSegment(BaseModel):
    session_id: str
    track: Literal["mic", "system"]
    start_ms: int
    end_ms: int
    frames: int
    pcm_base64_frames: list[str] = []


class AsrResult(BaseModel):
    text: str
    language: str | None = None
    start_ms: int
    end_ms: int
    confidence: float | None = None
    is_final: bool = True


class AsrProvider(ABC):
    @abstractmethod
    async def transcribe_segment(self, segment: SpeechSegment) -> AsrResult:
        pass
