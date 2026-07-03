from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.mock_provider import MockAsrProvider
from app.audio.frame import AudioFrame
from app.diarization.router import DiarizationRouter
from app.events.suggestion_engine import SuggestionEngine
from app.schemas.websocket import WebSocketEnvelope
from app.storage.repositories import MeetingRepository, SuggestionRepository, TranscriptRepository
from app.transcript.processor import build_transcript_payload
from app.transcript.segmenter import TranscriptSegmenter
from app.vad.mock_provider import MockVadProvider

router = APIRouter()

vad_provider = MockVadProvider()
asr_provider = MockAsrProvider()
diarization_provider = DiarizationRouter()
meeting_repo = MeetingRepository()
transcript_repo = TranscriptRepository()
suggestion_repo = SuggestionRepository()
suggestion_engine = SuggestionEngine()


@router.websocket("/ws/meetings/{session_id}")
async def meeting_socket(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    if meeting_repo.get(session_id) is None:
        meeting_repo.create(
            meeting_id=session_id,
            title="WebSocket Meeting",
            mode="general",
            user_role="default",
        )
    segmenter = TranscriptSegmenter()
    try:
        await websocket.send_json(
            WebSocketEnvelope(
                type="meeting.status",
                session_id=session_id,
                timestamp=datetime.now(UTC),
                payload={
                    "status": "recording",
                    "micActive": True,
                    "systemActive": True,
                    "asrReady": True,
                    "llmReady": False,
                },
            ).model_dump(mode="json")
        )
        while True:
            incoming = await websocket.receive_json()
            if incoming.get("type") != "audio.frame":
                continue

            frame = AudioFrame.model_validate(incoming.get("payload", {}))
            vad = vad_provider.detect(frame)
            state, segment = segmenter.ingest(frame, vad)

            await websocket.send_json(
                WebSocketEnvelope(
                    type="audio.level",
                    session_id=session_id,
                    timestamp=datetime.now(UTC),
                    payload={
                        "track": frame.track,
                        "level": vad.level,
                        "isSpeech": vad.is_speech,
                        "framesReceived": state.frames_received,
                    },
                ).model_dump(mode="json")
            )

            if segment is None:
                continue

            asr_result = await asr_provider.transcribe_segment(segment)
            speaker = await diarization_provider.assign_speaker(segment)
            transcript_payload = build_transcript_payload(session_id, segment, asr_result, speaker)
            transcript_repo.create(session_id, transcript_payload)
            await websocket.send_json(
                WebSocketEnvelope(
                    type="transcript.final",
                    session_id=session_id,
                    timestamp=datetime.now(UTC),
                    payload=transcript_payload,
                ).model_dump(mode="json")
            )

            meeting = meeting_repo.get(session_id) or {}
            event, suggestion_payload = await suggestion_engine.maybe_create_suggestion(
                session_id=session_id,
                meeting=meeting,
                transcript=transcript_payload,
            )
            if event.should_suggest:
                await websocket.send_json(
                    WebSocketEnvelope(
                        type="analysis.event",
                        session_id=session_id,
                        timestamp=datetime.now(UTC),
                        payload={
                            "eventType": event.event_type,
                            "priority": event.priority,
                            "reason": event.reason,
                            "triggerSegmentId": transcript_payload["segmentId"],
                        },
                    ).model_dump(mode="json")
                )

            if suggestion_payload is not None:
                suggestion_repo.create(session_id, suggestion_payload)
                await websocket.send_json(
                    WebSocketEnvelope(
                        type="suggestion.created",
                        session_id=session_id,
                        timestamp=datetime.now(UTC),
                        payload=suggestion_payload,
                    ).model_dump(mode="json")
                )
    except WebSocketDisconnect:
        return
