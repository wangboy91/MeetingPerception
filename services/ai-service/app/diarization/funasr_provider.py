import os
from pathlib import Path
from typing import Any

from app.asr.base import SpeechSegment
from app.diarization.audio_utils import segment_to_wav_file
from app.diarization.base import DiarizationProvider, SpeakerLabel


class FunAsrDiarizationProvider(DiarizationProvider):
    def __init__(self) -> None:
        self._model: Any | None = None
        self._speaker_map: dict[str, int] = {}

    async def assign_speaker(self, segment: SpeechSegment) -> SpeakerLabel:
        if segment.track == "mic":
            return SpeakerLabel(speaker_id="me", label="Me", source="mic")

        wav_path = segment_to_wav_file(segment)
        try:
            model = self._load_model()
            result = model.generate(input=str(wav_path))
            speaker_key = _dominant_funasr_speaker(result)
            speaker_index = self._speaker_index(speaker_key)
            return SpeakerLabel(
                speaker_id=f"remote-speaker-{speaker_index}",
                label=f"Speaker {speaker_index}",
                source="system",
            )
        finally:
            _unlink_quietly(wav_path)

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from funasr import AutoModel
        except ImportError as exc:
            raise RuntimeError("FunASR diarization requires `funasr` to be installed.") from exc

        model_name = os.getenv(
            "MEETING_COPILOT_FUNASR_DIARIZATION_MODEL",
            "iic/speech_paraformer-large-vad-punc-spk_asr_nat-zh-cn",
        )
        self._model = AutoModel(model=model_name)
        return self._model

    def _speaker_index(self, speaker_key: str) -> int:
        if speaker_key not in self._speaker_map:
            self._speaker_map[speaker_key] = len(self._speaker_map) + 1
        return self._speaker_map[speaker_key]


def _dominant_funasr_speaker(result: Any) -> str:
    items = result if isinstance(result, list) else [result]
    durations: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        for sentence in item.get("sentence_info", []) or []:
            speaker = str(sentence.get("spk") or sentence.get("speaker") or "remote")
            start = int(sentence.get("start") or 0)
            end = int(sentence.get("end") or start)
            durations[speaker] = durations.get(speaker, 0) + max(1, end - start)
    if not durations:
        return "remote"
    return max(durations.items(), key=lambda item: item[1])[0]


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass
