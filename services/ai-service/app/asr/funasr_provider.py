from app.asr.base import AsrProvider, AsrResult, SpeechSegment


class FunAsrProvider(AsrProvider):
    async def transcribe_segment(self, segment: SpeechSegment) -> AsrResult:
        raise NotImplementedError("FunASR provider skeleton is reserved for the real ASR phase.")
