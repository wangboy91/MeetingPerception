from app.asr.base import SpeechSegment
from app.diarization.base import DiarizationProvider, SpeakerLabel


class MockDiarizationProvider(DiarizationProvider):
    async def assign_speaker(self, segment: SpeechSegment) -> SpeakerLabel:
        if segment.track == "mic":
            return SpeakerLabel(speaker_id="me", label="Me", source="mic")

        # MVP: system output is a remote mixed track. We do not infer real names.
        return SpeakerLabel(speaker_id="remote", label="Remote", source="system")
