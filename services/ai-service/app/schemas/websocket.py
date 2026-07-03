from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WebSocketEnvelope(BaseModel):
    type: Literal[
        "meeting.status",
        "transcript.partial",
        "transcript.final",
        "analysis.event",
        "suggestion.created",
        "summary.updated",
        "audio.level",
        "audio.frame",
        "error",
    ]
    session_id: str = Field(serialization_alias="session_id")
    timestamp: datetime
    payload: dict[str, Any]
