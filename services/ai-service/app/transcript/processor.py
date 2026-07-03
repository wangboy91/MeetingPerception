from datetime import UTC, datetime
from uuid import uuid4

from app.asr.base import AsrResult, SpeechSegment
from app.diarization.base import SpeakerLabel


def format_time(ms: int) -> str:
    total_seconds = max(0, ms // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"00:{minutes:02d}:{seconds:02d}"


def build_transcript_payload(
    session_id: str,
    segment: SpeechSegment,
    result: AsrResult,
    speaker: SpeakerLabel,
) -> dict:
    transcript_id = str(uuid4())
    return {
        "id": transcript_id,
        "segmentId": transcript_id,
        "sessionId": session_id,
        "time": format_time(result.end_ms),
        "speakerId": speaker.speaker_id,
        "speaker": speaker.label,
        "speakerSource": speaker.source,
        "track": segment.track,
        "startMs": result.start_ms,
        "endMs": result.end_ms,
        "confidence": result.confidence,
        "text": result.text,
        "isFinal": result.is_final,
        "createdAt": datetime.now(UTC).isoformat(),
    }
