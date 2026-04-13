from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogItemResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None = None
    actor_user_id: int | None = None
    actor_username: str | None = None
    target_user_id: int | None = None
    target_username: str | None = None
    details: dict | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItemResponse]
    total: int
