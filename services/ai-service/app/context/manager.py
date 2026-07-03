from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.events.detector import DetectedEvent


@dataclass
class MeetingContext:
    current_topic: str = "未识别"
    recent_transcripts: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=80))
    decisions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    last_suggestion_ms_by_type: dict[str, int] = field(default_factory=dict)

    def as_prompt_state(self) -> dict[str, Any]:
        return {
            "current_topic": self.current_topic,
            "decisions": self.decisions[-8:],
            "risks": self.risks[-8:],
            "todos": self.todos[-8:],
            "open_questions": self.open_questions[-8:],
        }


class ContextManager:
    def __init__(self) -> None:
        self._sessions: dict[str, MeetingContext] = {}

    def get(self, session_id: str) -> MeetingContext:
        return self._sessions.setdefault(session_id, MeetingContext())

    def update_with_transcript(
        self,
        session_id: str,
        transcript: dict[str, Any],
        event: DetectedEvent,
    ) -> MeetingContext:
        context = self.get(session_id)
        context.recent_transcripts.append(transcript)
        text = transcript["text"]

        if context.current_topic == "未识别" and len(text) > 6:
            context.current_topic = text[:24]
        if event.event_type == "decision":
            _append_unique(context.decisions, text)
        if event.event_type in {"risk", "time_conflict", "scope_conflict", "technical_unknown"}:
            _append_unique(context.risks, text)
        if event.event_type == "action_item":
            _append_unique(context.todos, text)
        if event.event_type == "question":
            _append_unique(context.open_questions, text)

        return context

    def can_suggest(self, session_id: str, event: DetectedEvent, now_ms: int) -> bool:
        if not event.should_suggest or event.priority == "low":
            return False
        context = self.get(session_id)
        last_ms = context.last_suggestion_ms_by_type.get(event.event_type)
        if last_ms is not None and now_ms - last_ms < 60_000:
            return False
        context.last_suggestion_ms_by_type[event.event_type] = now_ms
        return True


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
