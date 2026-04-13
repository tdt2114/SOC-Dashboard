from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AlertWorkflowUserOption(BaseModel):
    id: int
    username: str
    full_name: str | None = None


class AlertAssignmentInfo(BaseModel):
    user_id: int | None = None
    username: str | None = None
    full_name: str | None = None
    updated_at: datetime | None = None


class AlertNoteInfo(BaseModel):
    id: int
    author_user_id: int
    author_username: str
    author_full_name: str | None = None
    body: str
    created_at: datetime


class AlertWorkflowResponse(BaseModel):
    alert_id: str
    assignee: AlertAssignmentInfo
    assignee_options: list[AlertWorkflowUserOption]
    notes: list[AlertNoteInfo]


class AlertAssignmentRequest(BaseModel):
    assigned_user_id: int | None = None


class AlertNoteCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
