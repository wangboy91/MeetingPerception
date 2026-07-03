import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.context.manager import ContextManager, MeetingContext
from app.events.detector import DetectedEvent, EventDetector
from app.llm.router import LlmRouter

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
SUGGESTION_SCHEMA = {
    "title": "string",
    "problem_essence": "string",
    "risk": "string",
    "suggested_reply": "string",
    "follow_up_question": "string",
    "action_item": "string",
    "priority": "low|medium|high",
}


class SuggestionEngine:
    def __init__(self) -> None:
        self.detector = EventDetector()
        self.context_manager = ContextManager()
        self.llm_router = LlmRouter()
        self.system_prompt = _read_prompt("suggestion_generator.md")

    async def maybe_create_suggestion(
        self,
        session_id: str,
        meeting: dict[str, Any],
        transcript: dict[str, Any],
    ) -> tuple[DetectedEvent, dict[str, Any] | None]:
        event = self.detector.detect(transcript["text"])
        context = self.context_manager.update_with_transcript(session_id, transcript, event)
        now_ms = int(transcript.get("endMs") or 0)
        if not self.context_manager.can_suggest(session_id, event, now_ms):
            return event, None

        user_prompt = _build_user_prompt(meeting, context, transcript, event)
        result = await self.llm_router.complete_json(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema=SUGGESTION_SCHEMA,
        )
        return event, _normalize_suggestion(session_id, transcript, event, result)


def _read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _build_user_prompt(
    meeting: dict[str, Any],
    context: MeetingContext,
    transcript: dict[str, Any],
    event: DetectedEvent,
) -> str:
    recent = list(context.recent_transcripts)[-12:]
    payload = {
        "user_role": meeting.get("user_role", "default"),
        "meeting_mode": meeting.get("mode", "general"),
        "current_topic": context.current_topic,
        "meeting_state": context.as_prompt_state(),
        "recent_transcript": [
            {"speaker": item.get("speaker"), "text": item.get("text"), "time": item.get("time")}
            for item in recent
        ],
        "trigger_event": {
            "event_type": event.event_type,
            "priority": event.priority,
            "reason": event.reason,
            "text": transcript["text"],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _normalize_suggestion(
    session_id: str,
    transcript: dict[str, Any],
    event: DetectedEvent,
    result: dict[str, Any],
) -> dict[str, Any]:
    priority = result.get("priority") if result.get("priority") in {"low", "medium", "high"} else event.priority
    problem_essence = str(result.get("problem_essence") or event.reason)
    suggested_reply = str(result.get("suggested_reply") or "建议先确认影响范围、责任人和下一步动作。")
    follow_up_question = str(result.get("follow_up_question") or "")
    action_item = str(result.get("action_item") or "")
    risk = str(result.get("risk") or "")
    return {
        "id": str(uuid4()),
        "sessionId": session_id,
        "triggerSegmentId": transcript["segmentId"],
        "eventType": event.event_type,
        "priority": priority,
        "title": str(result.get("title") or "建议现场确认"),
        "problemEssence": problem_essence,
        "rationale": problem_essence,
        "risk": risk,
        "recommendedResponse": suggested_reply,
        "suggestedReply": suggested_reply,
        "followUpQuestion": follow_up_question,
        "actionItem": action_item,
        "createdAt": datetime.now(UTC).isoformat(),
    }
