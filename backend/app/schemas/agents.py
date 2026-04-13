from __future__ import annotations

from pydantic import BaseModel

from app.schemas.alerts import AlertListItem


class AgentListItem(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    last_keepalive: str | None = None
    platform: str | None = None


class AgentListResponse(BaseModel):
    items: list[AgentListItem]
    total: int


class AgentMonitoringContext(BaseModel):
    total_alerts_24h: int
    high_or_critical_alerts_24h: int
    status: str | None = None


class AgentDetailResponse(BaseModel):
    agent: AgentListItem
    recent_alerts: list[AlertListItem]
    monitoring_context: AgentMonitoringContext
