from __future__ import annotations

from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from app.db.models import RefreshToken, User, UserRole
from app.schemas.auth import AuthProfileUpdateRequest, AuthTokenResponse, AuthUserResponse
from app.services.audit import write_audit_log


WORKFLOW_ROLES = {"analyst", "admin"}


def serialize_user(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        department=user.department.name if user.department else None,
        roles=[item.role.name for item in user.roles],
    )


async def get_user_by_identity(session: AsyncSession, identity: str) -> User | None:
    query = (
        select(User)
        .where((User.username == identity) | (User.email == identity))
        .options(
            selectinload(User.department),
            selectinload(User.roles).selectinload(UserRole.role),
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, username: str, password: str) -> User:
    user = await get_user_by_identity(session, username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


async def issue_tokens(session: AsyncSession, user: User) -> AuthTokenResponse:
    access_token = create_access_token(subject=user.username, user_id=user.id)
    refresh_token, token_id, expires_at = create_refresh_token(subject=user.username, user_id=user.id)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_id=token_id,
            expires_at=expires_at,
        )
    )
    await write_audit_log(
        session,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        target_user_id=user.id,
        details={"username": user.username},
    )
    await session.commit()
    await session.refresh(user)
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=serialize_user(user),
    )


async def rotate_refresh_token(session: AsyncSession, refresh_token: str) -> AuthTokenResponse:
    try:
        payload = decode_refresh_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid") from exc
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    token_id = payload.get("jti")
    user_id = payload.get("user_id")
    query = (
        select(RefreshToken)
        .where(RefreshToken.token_id == token_id, RefreshToken.user_id == user_id)
        .options(
            selectinload(RefreshToken.user).selectinload(User.department),
            selectinload(RefreshToken.user).selectinload(User.roles).selectinload(UserRole.role),
        )
    )
    result = await session.execute(query)
    stored = result.scalar_one_or_none()
    if stored is None or stored.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")
    if stored.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    stored.revoked_at = datetime.now(UTC)
    user = stored.user
    access_token = create_access_token(subject=user.username, user_id=user.id)
    new_refresh_token, new_token_id, new_expires_at = create_refresh_token(subject=user.username, user_id=user.id)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_id=new_token_id,
            expires_at=new_expires_at,
        )
    )
    await session.commit()
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=serialize_user(user),
    )


async def revoke_refresh_token(session: AsyncSession, refresh_token: str) -> None:
    try:
        payload = decode_refresh_token(refresh_token)
    except jwt.PyJWTError:
        return
    token_id = payload.get("jti")
    query = select(RefreshToken).where(RefreshToken.token_id == token_id)
    result = await session.execute(query)
    stored = result.scalar_one_or_none()
    if stored is None:
        return
    stored.revoked_at = datetime.now(UTC)
    await write_audit_log(
        session,
        action="auth.logout",
        entity_type="user",
        entity_id=stored.user_id,
        actor_user_id=stored.user_id,
        target_user_id=stored.user_id,
        details={"token_id": stored.token_id},
    )
    await session.commit()


async def get_current_user_from_token(session: AsyncSession, access_token: str) -> AuthUserResponse:
    user = await get_current_user_model_from_token(session, access_token)
    return serialize_user(user)


async def get_current_user_model_from_token(session: AsyncSession, access_token: str) -> User:
    try:
        payload = decode_access_token(access_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is invalid") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("user_id")
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.department),
            selectinload(User.roles).selectinload(UserRole.role),
        )
    )
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")
    return user


def user_has_any_role(user: User, role_names: set[str]) -> bool:
    if user.is_superuser:
        return True
    return any(item.role.name in role_names for item in user.roles)


def require_user_roles(user: User, role_names: set[str], *, detail: str) -> User:
    if not user_has_any_role(user, role_names):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return user


async def update_current_user_profile(
    session: AsyncSession,
    user: User,
    payload: AuthProfileUpdateRequest,
) -> AuthUserResponse:
    result = await session.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing is not None and existing.id != user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")

    user.email = payload.email
    user.full_name = payload.full_name
    await session.commit()
    await session.refresh(user)
    refreshed = await get_user_by_identity(session, user.username)
    return serialize_user(refreshed or user)


async def change_current_user_password(
    session: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(new_password)
    await session.commit()
