from __future__ import annotations

from pydantic import BaseModel

from app.schemas.alerts import AlertListItem


class DashboardSummaryResponse(BaseModel):
    total_alerts_24h: int
    high_or_critical_alerts_24h: int
    active_agents: int
    disconnected_agents: int
    total_agents: int
    open_cases: int
    assigned_to_me_alerts: int
    recent_high_alerts: list[AlertListItem]
