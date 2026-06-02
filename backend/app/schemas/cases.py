from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CaseAlertItemResponse(BaseModel):
    id: int
    alert_id: str
    created_at: datetime


class CaseCommentItemResponse(BaseModel):
    id: int
    author_user_id: int
    author_username: str
    author_full_name: str | None = None
    body: str
    created_at: datetime


class CaseItemResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: str
    severity: str
    owner_user_id: int | None = None
    owner_username: str | None = None
    owner_full_name: str | None = None
    created_by_user_id: int | None = None
    created_by_username: str | None = None
    alert_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime


class CaseDetailResponse(CaseItemResponse):
    alerts: list[CaseAlertItemResponse]
    comments: list[CaseCommentItemResponse]


class CaseListResponse(BaseModel):
    items: list[CaseItemResponse]
    total: int


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = "open"
    severity: str = "medium"
    owner_user_id: int | None = None
    alert_id: str | None = None


class CaseUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    severity: str | None = None
    owner_user_id: int | None = None


class CaseAlertCreateRequest(BaseModel):
    alert_id: str = Field(min_length=1)


class CaseCommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
