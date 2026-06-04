from __future__ import annotations

import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UpstreamServiceError
from app.db.session import get_db_session
from app.schemas.alerts import AlertListItem
from app.services.audit_logs import list_audit_logs
from app.services.auth import WORKFLOW_ROLES, get_current_user_model_from_token, require_user_roles
from app.services.cases import list_cases
from app.services.indexer import IndexerClient
from app.services.mock_data import MockDataService
from app.services.users import require_superadmin_user

router = APIRouter(prefix="/api/exports", tags=["exports"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _current_user(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return await get_current_user_model_from_token(session, credentials.credentials)


def _csv_response(filename: str, headers: list[str], rows: list[list[object | None]]) -> Response:
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/alerts.csv")
async def export_alerts_csv(
    time_range: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    rule_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await _current_user(credentials, session)
    client = MockDataService() if settings.mock_mode else IndexerClient(settings)
    try:
        result = await client.search_alerts(
            page=1,
            page_size=settings.max_page_size,
            time_range=time_range or settings.default_time_range,
            severity=severity,
            agent_id=agent_id,
            agent_name=agent_name,
            rule_id=rule_id,
            query_text=q,
        )
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=f"{exc.service} unavailable: {exc.message}") from exc

    return _csv_response(
        "alerts.csv",
        ["id", "timestamp", "severity", "agent_id", "agent_name", "rule_id", "rule_level", "description", "srcip", "path"],
        [_alert_row(item) for item in result.items],
    )


@router.get("/cases.csv")
async def export_cases_csv(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    current_user = await _current_user(credentials, session)
    require_user_roles(current_user, WORKFLOW_ROLES, detail="Case export requires analyst or admin access")
    result = await list_cases(session)
    return _csv_response(
        "cases.csv",
        ["id", "title", "status", "severity", "owner", "alerts", "comments", "created_at", "updated_at"],
        [
            [
                item.id,
                item.title,
                item.status,
                item.severity,
                item.owner_username,
                item.alert_count,
                item.comment_count,
                item.created_at,
                item.updated_at,
            ]
            for item in result.items
        ],
    )


@router.get("/audit-logs.csv")
async def export_audit_logs_csv(
    action: str | None = Query(default=None),
    q: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    current_user = await _current_user(credentials, session)
    await require_superadmin_user(current_user)
    result = await list_audit_logs(session, action=action, q=q, page=1, page_size=100)
    return _csv_response(
        "audit-logs.csv",
        ["id", "created_at", "action", "actor", "target", "entity_type", "entity_id", "details"],
        [
            [
                item.id,
                item.created_at,
                item.action,
                item.actor_username,
                item.target_username,
                item.entity_type,
                item.entity_id,
                item.details,
            ]
            for item in result.items
        ],
    )


def _alert_row(item: AlertListItem) -> list[object | None]:
    return [
        item.id,
        item.timestamp,
        item.severity_label,
        item.agent.id,
        item.agent.name,
        item.rule.id,
        item.rule.level,
        item.rule.description,
        item.source.srcip,
        item.file.path,
    ]
