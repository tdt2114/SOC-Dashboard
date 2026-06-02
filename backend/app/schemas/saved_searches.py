from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedSearchItemResponse(BaseModel):
    id: int
    name: str
    filters: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SavedSearchListResponse(BaseModel):
    items: list[SavedSearchItemResponse]
    total: int


class SavedSearchCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    filters: dict[str, Any]


class SavedSearchUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    filters: dict[str, Any] | None = None
