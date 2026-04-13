from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import (
    AuthChangePasswordRequest,
    AuthLoginRequest,
    AuthLogoutRequest,
    AuthProfileUpdateRequest,
    AuthRefreshRequest,
    AuthTokenResponse,
    AuthUserResponse,
)
from app.services.auth import (
    authenticate_user,
    change_current_user_password,
    get_current_user_from_token,
    get_current_user_model_from_token,
    issue_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    update_current_user_profile,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: AuthLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    user = await authenticate_user(session, payload.username, payload.password)
    return await issue_tokens(session, user)


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(
    payload: AuthRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    return await rotate_refresh_token(session, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: AuthLogoutRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await revoke_refresh_token(session, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AuthUserResponse)
async def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AuthUserResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return await get_current_user_from_token(session, credentials.credentials)


@router.patch("/me", response_model=AuthUserResponse)
async def update_me(
    payload: AuthProfileUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AuthUserResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    return await update_current_user_profile(session, current_user, payload)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: AuthChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    current_user = await get_current_user_model_from_token(session, credentials.credentials)
    await change_current_user_password(session, current_user, payload.current_password, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
