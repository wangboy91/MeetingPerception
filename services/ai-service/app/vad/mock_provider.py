from app.audio.frame import AudioFrame
from app.vad.base import VadProvider, VadResult


class MockVadProvider(VadProvider):
    def __init__(self, threshold: float = 0.018) -> None:
        self.threshold = threshold

    def detect(self, frame: AudioFrame) -> VadResult:
        level = max(0.0, min(1.0, frame.rms))
        return VadResult(is_speech=level >= self.threshold, level=level)
