from app.asr.base import SpeechSegment
from app.diarization.base import DiarizationProvider, SpeakerLabel
from app.diarization.funasr_provider import FunAsrDiarizationProvider
from app.diarization.mock_provider import MockDiarizationProvider
from app.diarization.pyannote_provider import PyannoteDiarizationProvider
from app.storage.repositories import SettingsRepository


class DiarizationRouter(DiarizationProvider):
    def __init__(self) -> None:
        self.mock = MockDiarizationProvider()
        self._providers: dict[str, DiarizationProvider] = {
            "mock": self.mock,
            "funasr": FunAsrDiarizationProvider(),
            "pyannote": PyannoteDiarizationProvider(),
        }

    async def assign_speaker(self, segment: SpeechSegment) -> SpeakerLabel:
        provider_name = _configured_provider()
        provider = self._providers.get(provider_name, self.mock)
        try:
            return await provider.assign_speaker(segment)
        except Exception:
            return await self.mock.assign_speaker(segment)


def _configured_provider() -> str:
    try:
        stored = SettingsRepository().get("app") or {}
    except Exception:
        return "mock"
    provider = str(stored.get("diarizationProvider", "mock")).strip()
    return provider if provider in {"mock", "funasr", "pyannote"} else "mock"
