from __future__ import annotations

from pydantic import BaseModel


class AgentListItem(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    last_keepalive: str | None = None


class AgentListResponse(BaseModel):
    items: list[AgentListItem]
    total: int
