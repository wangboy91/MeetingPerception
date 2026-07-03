from app.audio.frame import AudioFrame
from app.vad.base import VadProvider, VadResult


class SileroVadProvider(VadProvider):
    def detect(self, frame: AudioFrame) -> VadResult:
        raise NotImplementedError("Silero VAD will be wired after the mock pipeline is stable.")
