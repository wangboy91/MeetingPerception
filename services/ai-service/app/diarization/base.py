from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.asr.base import SpeechSegment


class SpeakerLabel(BaseModel):
    speaker_id: str
    label: str
    source: str


class DiarizationProvider(ABC):
    @abstractmethod
    async def assign_speaker(self, segment: SpeechSegment) -> SpeakerLabel:
        pass
