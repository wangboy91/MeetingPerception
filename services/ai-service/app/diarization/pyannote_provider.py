import os
from pathlib import Path
from typing import Any

from app.asr.base import SpeechSegment
from app.diarization.audio_utils import segment_to_wav_file
from app.diarization.base import DiarizationProvider, SpeakerLabel


class PyannoteDiarizationProvider(DiarizationProvider):
    def __init__(self) -> None:
        self._pipeline: Any | None = None
        self._speaker_map: dict[str, int] = {}

    async def assign_speaker(self, segment: SpeechSegment) -> SpeakerLabel:
        if segment.track == "mic":
            return SpeakerLabel(speaker_id="me", label="Me", source="mic")

        wav_path = segment_to_wav_file(segment)
        try:
            pipeline = self._load_pipeline()
            diarization = pipeline(str(wav_path))
            speaker_key = _dominant_pyannote_speaker(diarization)
            speaker_index = self._speaker_index(speaker_key)
            return SpeakerLabel(
                speaker_id=f"remote-speaker-{speaker_index}",
                label=f"Speaker {speaker_index}",
                source="system",
            )
        finally:
            _unlink_quietly(wav_path)

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        try:
            from pyannote.audio import Pipeline
        except ImportError as exc:
            raise RuntimeError("Pyannote diarization requires `pyannote.audio` to be installed.") from exc

        model_name = os.getenv("MEETING_COPILOT_PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1")
        token = os.getenv("MEETING_COPILOT_PYANNOTE_TOKEN") or os.getenv("HF_TOKEN")
        self._pipeline = Pipeline.from_pretrained(model_name, use_auth_token=token)
        return self._pipeline

    def _speaker_index(self, speaker_key: str) -> int:
        if speaker_key not in self._speaker_map:
            self._speaker_map[speaker_key] = len(self._speaker_map) + 1
        return self._speaker_map[speaker_key]


def _dominant_pyannote_speaker(diarization: Any) -> str:
    durations: dict[str, float] = {}
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speaker_key = str(speaker)
        durations[speaker_key] = durations.get(speaker_key, 0.0) + max(0.0, turn.end - turn.start)
    if not durations:
        return "remote"
    return max(durations.items(), key=lambda item: item[1])[0]


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass
