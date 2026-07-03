from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from app.core.config import llm_settings
from app.schemas.meeting import (
    CreateMeetingRequest,
    CreateMeetingResponse,
    HealthResponse,
    StopMeetingResponse,
)
from app.schemas.settings import AppSettings
from app.storage.database import database_path
from app.storage.exporter import export_meeting_markdown
from app.storage.repositories import (
    MeetingRepository,
    SettingsRepository,
    SpeakerRepository,
    SuggestionRepository,
    TranscriptRepository,
)

router = APIRouter()
meeting_repo = MeetingRepository()
transcript_repo = TranscriptRepository()
suggestion_repo = SuggestionRepository()
speaker_repo = SpeakerRepository()
settings_repo = SettingsRepository()
SETTINGS_KEY = "app"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-service")


@router.post("/api/meetings", response_model=CreateMeetingResponse)
async def create_meeting(request: CreateMeetingRequest | None = None) -> CreateMeetingResponse:
    now = datetime.now(UTC)
    meeting_id = str(uuid4())
    request = request or CreateMeetingRequest()
    meeting = meeting_repo.create(
        meeting_id=meeting_id,
        title=request.title,
        mode=request.mode,
        user_role=request.user_role,
    )
    return CreateMeetingResponse(
        id=meeting["id"],
        status=meeting["status"],
        started_at=datetime.fromisoformat(meeting["started_at"]) if meeting["started_at"] else now,
    )


@router.get("/api/meetings")
async def list_meetings() -> list[dict]:
    return meeting_repo.list_recent()


@router.delete("/api/meetings")
async def delete_all_meetings() -> dict[str, int]:
    deleted = meeting_repo.delete_all()
    return {"deleted": deleted}


@router.get("/api/settings", response_model=AppSettings, response_model_by_alias=True)
async def get_settings() -> AppSettings:
    return _load_app_settings()


@router.put("/api/settings", response_model=AppSettings, response_model_by_alias=True)
async def update_settings(payload: AppSettings) -> AppSettings:
    current = _load_app_settings()
    next_settings = current.model_copy(
        update={
            "asr_provider": payload.asr_provider,
            "diarization_provider": payload.diarization_provider,
            "llm_provider": payload.llm_provider,
            "llm_base_url": payload.llm_base_url,
            "llm_model": payload.llm_model,
            "cloud_llm_enabled": payload.cloud_llm_enabled,
            "store_transcript": payload.store_transcript,
            "debug_log_transcript": payload.debug_log_transcript,
        }
    )
    settings_repo.set(SETTINGS_KEY, _persisted_settings(next_settings))
    return _load_app_settings()


@router.get("/api/meetings/{session_id}")
async def get_meeting(session_id: str) -> dict:
    meeting = meeting_repo.get(session_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/api/meetings/{session_id}/stop", response_model=StopMeetingResponse)
async def stop_meeting(session_id: str) -> StopMeetingResponse:
    meeting = meeting_repo.stop(session_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return StopMeetingResponse(
        session_id=session_id,
        status=meeting["status"],
        summary_status="pending",
    )


@router.get("/api/meetings/{session_id}/transcripts")
async def get_transcripts(session_id: str) -> list[dict]:
    if meeting_repo.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return transcript_repo.list_for_meeting(session_id)


@router.get("/api/meetings/{session_id}/suggestions")
async def get_suggestions(session_id: str) -> list[dict]:
    if meeting_repo.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return suggestion_repo.list_for_meeting(session_id)


@router.get("/api/meetings/{session_id}/speakers")
async def get_speakers(session_id: str) -> list[dict]:
    if meeting_repo.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return speaker_repo.list_for_meeting(session_id)


@router.patch("/api/meetings/{session_id}/speakers/{speaker_id}")
async def rename_speaker(session_id: str, speaker_id: str, payload: dict) -> dict:
    if meeting_repo.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    speaker = speaker_repo.rename(
        meeting_id=session_id,
        speaker_id=speaker_id,
        display_name=str(payload.get("displayName", "")),
    )
    if speaker is None:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return speaker


@router.get("/api/meetings/{session_id}/export")
async def export_meeting(session_id: str, format: str = "markdown") -> PlainTextResponse:
    if format != "markdown":
        raise HTTPException(status_code=400, detail="Only markdown export is supported")
    meeting = meeting_repo.get(session_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    markdown = export_meeting_markdown(meeting)
    return PlainTextResponse(
        markdown,
        headers={
            "Content-Disposition": f'attachment; filename="{session_id}.md"',
        },
    )


@router.delete("/api/meetings/{session_id}")
async def delete_meeting(session_id: str) -> Response:
    deleted = meeting_repo.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return Response(status_code=204)


def _load_app_settings() -> AppSettings:
    llm = llm_settings()
    stored = settings_repo.get(SETTINGS_KEY) or {}
    settings = AppSettings(
        asrProvider=stored.get("asrProvider", "mock"),
        diarizationProvider=stored.get("diarizationProvider", "mock"),
        llmProvider=stored.get("llmProvider", llm.provider),
        llmBaseUrl=stored.get("llmBaseUrl", llm.base_url),
        llmModel=stored.get("llmModel", llm.model),
        cloudLlmEnabled=stored.get("cloudLlmEnabled", llm.cloud_enabled),
        storeTranscript=stored.get("storeTranscript", True),
        debugLogTranscript=stored.get("debugLogTranscript", False),
        dataDir=str(database_path().parent),
        apiKeyConfigured=bool(llm.api_key),
    )
    if not settings.api_key_configured and settings.llm_provider != "mock":
        settings.cloud_llm_enabled = False
    return settings


def _persisted_settings(settings: AppSettings) -> dict[str, object]:
    return {
        "asrProvider": settings.asr_provider,
        "diarizationProvider": settings.diarization_provider,
        "llmProvider": settings.llm_provider,
        "llmBaseUrl": settings.llm_base_url,
        "llmModel": settings.llm_model,
        "cloudLlmEnabled": settings.cloud_llm_enabled,
        "storeTranscript": settings.store_transcript,
        "debugLogTranscript": settings.debug_log_transcript,
    }
