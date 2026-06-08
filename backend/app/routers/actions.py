from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.actions import (
    PendingActionCreatedResponse,
    PendingActionCreateRequest,
    PendingActionItemResponse,
    PendingActionListResponse,
    PendingActionRejectRequest,
)
from app.services.actions import (
    APPROVAL_ROLES,
    approve_pending_action,
    create_pending_action,
    get_pending_action,
    list_pending_actions,
    reject_pending_action,
)
from app.services.auth import WORKFLOW_ROLES, get_current_user_model_from_token, require_user_roles

router = APIRouter(prefix="/api/actions", tags=["actions"])
bearer_scheme = HTTPBearer(auto_error=False)


def _require_soar_token(provided: str | None) -> None:
    expected = get_settings().soar_webhook_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SOAR integration is not configured (SOAR_WEBHOOK_TOKEN unset).",
        )
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SOAR token")


async def _user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
    roles: set[str],
    detail: str,
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return require_user_roles(current_user, roles, detail=detail)


@router.post("", response_model=PendingActionCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_action_route(
    payload: PendingActionCreateRequest,
    x_soar_token: str | None = Header(default=None, alias="X-SOAR-Token"),
    session: AsyncSession = Depends(get_db_session),
) -> PendingActionCreatedResponse:
    _require_soar_token(x_soar_token)
    item = await create_pending_action(session, payload, requested_by="shuffle-soar")
    return PendingActionCreatedResponse(
        **item.model_dump(),
        approval_path=f"/api/actions/{item.token}/approve",
    )


@router.get("", response_model=PendingActionListResponse)
async def list_actions_route(
    status: str | None = None,
    case_id: int | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> PendingActionListResponse:
    await _user_from_token(credentials, session, WORKFLOW_ROLES, "Response actions require analyst or admin access")
    return await list_pending_actions(session, status_filter=status, case_id=case_id)


@router.get("/{token}", response_model=PendingActionItemResponse)
async def get_action_route(
    token: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> PendingActionItemResponse:
    await _user_from_token(credentials, session, WORKFLOW_ROLES, "Response actions require analyst or admin access")
    return await get_pending_action(session, token)


@router.post("/{token}/approve", response_model=PendingActionItemResponse)
async def approve_action_route(
    token: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> PendingActionItemResponse:
    current_user = await _user_from_token(
        credentials, session, APPROVAL_ROLES, "Approving response actions requires admin access"
    )
    return await approve_pending_action(session, current_user, token)


@router.post("/{token}/reject", response_model=PendingActionItemResponse)
async def reject_action_route(
    token: str,
    payload: PendingActionRejectRequest | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> PendingActionItemResponse:
    current_user = await _user_from_token(
        credentials, session, APPROVAL_ROLES, "Rejecting response actions requires admin access"
    )
    reason = payload.reason if payload else None
    return await reject_pending_action(session, current_user, token, reason)
