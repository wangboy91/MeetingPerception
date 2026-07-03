from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class CreateMeetingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: Literal["recording"]
    started_at: datetime


class CreateMeetingRequest(BaseModel):
    title: str = "Untitled Meeting"
    mode: str = "general"
    user_role: str = Field(default="default", alias="userRole")


class StopMeetingResponse(BaseModel):
    session_id: str
    status: str
    summary_status: Literal["pending"]
