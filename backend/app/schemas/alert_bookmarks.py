from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertBookmarkResponse(BaseModel):
    alert_id: str
    is_bookmarked: bool
    bookmark_id: int | None = None
    created_at: datetime | None = None
