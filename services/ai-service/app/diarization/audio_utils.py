import base64
import tempfile
import wave
from pathlib import Path

from app.asr.base import SpeechSegment


def segment_to_wav_file(segment: SpeechSegment) -> Path:
    if not segment.pcm_base64_frames:
        raise RuntimeError("Diarization requires PCM audio frames, but the segment has none.")

    pcm = b"".join(base64.b64decode(frame) for frame in segment.pcm_base64_frames if frame)
    if not pcm:
        raise RuntimeError("Diarization requires non-empty PCM audio.")

    temp = tempfile.NamedTemporaryFile(prefix="meeting-copilot-", suffix=".wav", delete=False)
    temp.close()
    path = Path(temp.name)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(pcm)
    return path
