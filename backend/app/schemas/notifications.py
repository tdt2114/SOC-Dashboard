from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationItemResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    link_url: str | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationItemResponse]
    unread_count: int
