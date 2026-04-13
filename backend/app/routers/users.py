from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.users import UserAdminItemResponse, UserAdminListResponse, UserCreateRequest, UserResetPasswordRequest, UserUpdateRequest
from app.services.auth import get_current_user_model_from_token
from app.services.users import create_user, list_users, require_superadmin_user, reset_user_password, update_user

router = APIRouter(prefix="/api/users", tags=["users"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _superadmin_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return await require_superadmin_user(current_user)


@router.get("", response_model=UserAdminListResponse)
async def get_users(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UserAdminListResponse:
    await _superadmin_from_token(credentials, session)
    return await list_users(session)


@router.post("", response_model=UserAdminItemResponse, status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: UserCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UserAdminItemResponse:
    actor_user = await _superadmin_from_token(credentials, session)
    return await create_user(session, actor_user, payload)


@router.patch("/{user_id}", response_model=UserAdminItemResponse)
async def update_user_route(
    user_id: int,
    payload: UserUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UserAdminItemResponse:
    actor_user = await _superadmin_from_token(credentials, session)
    return await update_user(session, actor_user, user_id, payload)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password_route(
    user_id: int,
    payload: UserResetPasswordRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    actor_user = await _superadmin_from_token(credentials, session)
    await reset_user_password(session, actor_user, user_id, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
