from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.db.session import get_db_session
from app.schemas.alerts import AlertDetail, AlertListResponse
from app.schemas.alert_workflow import AlertAssignmentRequest, AlertNoteCreateRequest, AlertWorkflowResponse
from app.services.indexer import IndexerClient
from app.services.alert_workflow import add_alert_note, assign_alert, get_alert_workflow
from app.services.auth import get_current_user_model_from_token
from app.services.mock_data import MockDataService

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1),
    time_range: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    rule_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
) -> AlertListResponse:
    effective_page_size = min(page_size or settings.default_page_size, settings.max_page_size)
    client = MockDataService() if settings.mock_mode else IndexerClient(settings)
    try:
        return await client.search_alerts(
            page=page,
            page_size=effective_page_size,
            time_range=time_range or settings.default_time_range,
            severity=severity,
            agent_id=agent_id,
            agent_name=agent_name,
            rule_id=rule_id,
            query_text=q,
        )
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: str,
    settings: Settings = Depends(get_settings),
) -> AlertDetail:
    client = MockDataService() if settings.mock_mode else IndexerClient(settings)
    try:
        alert = await client.get_alert(alert_id)
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/{alert_id}/workflow", response_model=AlertWorkflowResponse)
async def get_workflow(
    alert_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AlertWorkflowResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    await get_current_user_model_from_token(session, credentials.credentials)
    return await get_alert_workflow(session, alert_id)


@router.patch("/{alert_id}/workflow/assignment", response_model=AlertWorkflowResponse)
async def update_assignment(
    alert_id: str,
    payload: AlertAssignmentRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AlertWorkflowResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return await assign_alert(session, alert_id=alert_id, actor_user=current_user, payload=payload)


@router.post("/{alert_id}/workflow/notes", response_model=AlertWorkflowResponse)
async def create_note(
    alert_id: str,
    payload: AlertNoteCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AlertWorkflowResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return await add_alert_note(session, alert_id=alert_id, actor_user=current_user, payload=payload)
