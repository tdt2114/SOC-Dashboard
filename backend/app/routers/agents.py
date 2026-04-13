from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.schemas.agents import AgentDetailResponse, AgentListResponse
from app.services.indexer import IndexerClient
from app.services.mock_data import MockDataService
from app.services.wazuh_api import WazuhApiClient

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
) -> AgentListResponse:
    client = MockDataService() if settings.mock_mode else WazuhApiClient(settings)
    try:
        return await client.list_agents(status=status, query_text=q)
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    settings: Settings = Depends(get_settings),
) -> AgentDetailResponse:
    if settings.mock_mode:
        client = MockDataService()
        agent_detail = await client.get_agent_detail(agent_id)
        if agent_detail is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent_detail

    agent_client = WazuhApiClient(settings)
    indexer_client = IndexerClient(settings)
    try:
        agent = await agent_client.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")

        recent_alerts = await indexer_client.search_alerts(
            page=1,
            page_size=5,
            time_range=settings.default_time_range,
            severity=None,
            agent_id=agent_id,
            agent_name=None,
            rule_id=None,
            query_text=None,
        )
        high_alerts = await indexer_client.search_alerts(
            page=1,
            page_size=1,
            time_range="24h",
            severity="high",
            agent_id=agent_id,
            agent_name=None,
            rule_id=None,
            query_text=None,
        )
        critical_alerts = await indexer_client.search_alerts(
            page=1,
            page_size=1,
            time_range="24h",
            severity="critical",
            agent_id=agent_id,
            agent_name=None,
            rule_id=None,
            query_text=None,
        )
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc

    return AgentDetailResponse(
        agent=agent,
        recent_alerts=recent_alerts.items,
        monitoring_context={
            "total_alerts_24h": recent_alerts.total,
            "high_or_critical_alerts_24h": high_alerts.total + critical_alerts.total,
            "status": agent.status,
        },
    )
