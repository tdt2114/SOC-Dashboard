from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AlertAssignment, Case, User
from app.schemas.alerts import AlertListItem
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.indexer import IndexerClient
from app.services.mock_data import MockDataService
from app.services.wazuh_api import WazuhApiClient


async def get_dashboard_summary(
    session: AsyncSession,
    current_user: User,
    settings: Settings,
) -> DashboardSummaryResponse:
    alert_client = MockDataService() if settings.mock_mode else IndexerClient(settings)
    agent_client = MockDataService() if settings.mock_mode else WazuhApiClient(settings)

    total_alerts = await alert_client.search_alerts(
        page=1,
        page_size=1,
        time_range="24h",
        severity=None,
        agent_id=None,
        agent_name=None,
        rule_id=None,
        query_text=None,
    )
    high_alerts = await alert_client.search_alerts(
        page=1,
        page_size=5,
        time_range="24h",
        severity="high",
        agent_id=None,
        agent_name=None,
        rule_id=None,
        query_text=None,
    )
    critical_alerts = await alert_client.search_alerts(
        page=1,
        page_size=5,
        time_range="24h",
        severity="critical",
        agent_id=None,
        agent_name=None,
        rule_id=None,
        query_text=None,
    )
    agents = await agent_client.list_agents(status=None, query_text=None)

    open_cases_result = await session.execute(select(func.count()).select_from(Case).where(Case.status != "closed"))
    assigned_result = await session.execute(
        select(func.count()).select_from(AlertAssignment).where(AlertAssignment.assigned_user_id == current_user.id)
    )

    recent_high_alerts = _sort_alerts([*critical_alerts.items, *high_alerts.items])[:5]
    active_agents = len([item for item in agents.items if (item.status or "").lower() == "active"])
    disconnected_agents = len([item for item in agents.items if (item.status or "").lower() == "disconnected"])

    return DashboardSummaryResponse(
        total_alerts_24h=total_alerts.total,
        high_or_critical_alerts_24h=high_alerts.total + critical_alerts.total,
        active_agents=active_agents,
        disconnected_agents=disconnected_agents,
        total_agents=agents.total,
        open_cases=int(open_cases_result.scalar_one() or 0),
        assigned_to_me_alerts=int(assigned_result.scalar_one() or 0),
        recent_high_alerts=recent_high_alerts,
    )


def _sort_alerts(items: list[AlertListItem]) -> list[AlertListItem]:
    return sorted(items, key=lambda item: item.timestamp or "", reverse=True)
