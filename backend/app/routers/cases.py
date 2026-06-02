from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.cases import (
    CaseAlertCreateRequest,
    CaseCommentCreateRequest,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseListResponse,
    CaseUpdateRequest,
)
from app.services.auth import WORKFLOW_ROLES, get_current_user_model_from_token, require_user_roles
from app.services.cases import (
    add_case_alert,
    add_case_comment,
    create_case,
    get_case,
    list_cases,
    remove_case_alert,
    update_case,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _workflow_user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return require_user_roles(current_user, WORKFLOW_ROLES, detail="Cases require analyst or admin access")


@router.get("", response_model=CaseListResponse)
async def get_cases(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseListResponse:
    await _workflow_user_from_token(credentials, session)
    return await list_cases(session)


@router.post("", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_case_route(
    payload: CaseCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await create_case(session, current_user, payload)


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case_route(
    case_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    await _workflow_user_from_token(credentials, session)
    return await get_case(session, case_id)


@router.patch("/{case_id}", response_model=CaseDetailResponse)
async def update_case_route(
    case_id: int,
    payload: CaseUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await update_case(session, current_user, case_id, payload)


@router.post("/{case_id}/alerts", response_model=CaseDetailResponse)
async def add_case_alert_route(
    case_id: int,
    payload: CaseAlertCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await add_case_alert(session, current_user, case_id, payload)


@router.delete("/{case_id}/alerts/{alert_id}", response_model=CaseDetailResponse)
async def remove_case_alert_route(
    case_id: int,
    alert_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await remove_case_alert(session, current_user, case_id, alert_id)


@router.post("/{case_id}/comments", response_model=CaseDetailResponse)
async def add_case_comment_route(
    case_id: int,
    payload: CaseCommentCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CaseDetailResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await add_case_comment(session, current_user, case_id, payload)
