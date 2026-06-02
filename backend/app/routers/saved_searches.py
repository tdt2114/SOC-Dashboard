from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.saved_searches import (
    SavedSearchCreateRequest,
    SavedSearchItemResponse,
    SavedSearchListResponse,
    SavedSearchUpdateRequest,
)
from app.services.auth import WORKFLOW_ROLES, get_current_user_model_from_token, require_user_roles
from app.services.saved_searches import (
    create_saved_search,
    delete_saved_search,
    list_saved_searches,
    update_saved_search,
)

router = APIRouter(prefix="/api/saved-searches", tags=["saved-searches"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _workflow_user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return require_user_roles(current_user, WORKFLOW_ROLES, detail="Saved searches require analyst or admin access")


@router.get("", response_model=SavedSearchListResponse)
async def get_saved_searches(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> SavedSearchListResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await list_saved_searches(session, current_user)


@router.post("", response_model=SavedSearchItemResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search_route(
    payload: SavedSearchCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> SavedSearchItemResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await create_saved_search(session, current_user, payload)


@router.patch("/{saved_search_id}", response_model=SavedSearchItemResponse)
async def update_saved_search_route(
    saved_search_id: int,
    payload: SavedSearchUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> SavedSearchItemResponse:
    current_user = await _workflow_user_from_token(credentials, session)
    return await update_saved_search(session, current_user, saved_search_id, payload)


@router.delete("/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search_route(
    saved_search_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    current_user = await _workflow_user_from_token(credentials, session)
    await delete_saved_search(session, current_user, saved_search_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
