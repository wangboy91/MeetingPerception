from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.audio.frame import AudioFrame


class VadResult(BaseModel):
    is_speech: bool
    level: float


class VadProvider(ABC):
    @abstractmethod
    def detect(self, frame: AudioFrame) -> VadResult:
        pass
