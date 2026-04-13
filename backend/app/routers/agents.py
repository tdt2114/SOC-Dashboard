from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.schemas.agents import AgentListResponse
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
