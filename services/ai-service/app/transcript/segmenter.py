from dataclasses import dataclass

from app.asr.base import SpeechSegment
from app.audio.frame import AudioFrame
from app.vad.base import VadResult


@dataclass
class TrackState:
    is_speaking: bool = False
    start_ms: int = 0
    last_speech_ms: int = 0
    speech_frames: int = 0
    silence_frames: int = 0
    emitted_segments: int = 0
    frames_received: int = 0
    pcm_base64_frames: list[str] | None = None


class TranscriptSegmenter:
    def __init__(self, min_speech_frames: int = 10, min_silence_frames: int = 8) -> None:
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames
        self._tracks: dict[str, TrackState] = {}

    def ingest(self, frame: AudioFrame, vad: VadResult) -> tuple[TrackState, SpeechSegment | None]:
        state = self._tracks.setdefault(frame.track, TrackState())
        state.frames_received += 1

        if vad.is_speech:
            if not state.is_speaking:
                state.is_speaking = True
                state.start_ms = frame.timestamp_ms
                state.speech_frames = 0
                state.silence_frames = 0
                state.pcm_base64_frames = []
            state.speech_frames += 1
            state.silence_frames = 0
            state.last_speech_ms = frame.timestamp_ms
            if state.pcm_base64_frames is not None and frame.data:
                state.pcm_base64_frames.append(frame.data)
            return state, None

        if not state.is_speaking:
            return state, None

        state.silence_frames += 1
        if state.silence_frames < self.min_silence_frames:
            return state, None

        segment = None
        if state.speech_frames >= self.min_speech_frames:
            segment = SpeechSegment(
                session_id=frame.session_id,
                track=frame.track,
                start_ms=state.start_ms,
                end_ms=state.last_speech_ms,
                frames=state.speech_frames,
                pcm_base64_frames=state.pcm_base64_frames or [],
            )
            state.emitted_segments += 1

        state.is_speaking = False
        state.speech_frames = 0
        state.silence_frames = 0
        state.pcm_base64_frames = None
        return state, segment
