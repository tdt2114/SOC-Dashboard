from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.models import Department, Role, User, UserRole
from app.schemas.users import (
    DepartmentOptionResponse,
    RoleOptionResponse,
    UserAdminItemResponse,
    UserAdminListResponse,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.services.audit import write_audit_log


def _validate_superuser_assignment(*, role_names: list[str], is_superuser: bool) -> None:
    if is_superuser and "admin" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Superadmin must also have the admin role",
        )


def _serialize_user_item(user: User) -> UserAdminItemResponse:
    return UserAdminItemResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        department=user.department.name if user.department else None,
        department_id=user.department_id,
        roles=[item.role.name for item in user.roles],
        created_at=user.created_at,
    )


async def require_superadmin_user(current_user: User) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin access required")
    return current_user


async def list_users(session: AsyncSession) -> UserAdminListResponse:
    user_result = await session.execute(
        select(User)
        .order_by(User.created_at.desc())
        .options(
            selectinload(User.department),
            selectinload(User.roles).selectinload(UserRole.role),
        )
    )
    users = list(user_result.scalars().unique().all())

    department_result = await session.execute(select(Department).order_by(Department.name.asc()))
    role_result = await session.execute(select(Role).order_by(Role.name.asc()))

    return UserAdminListResponse(
        items=[_serialize_user_item(user) for user in users],
        total=len(users),
        departments=[
            DepartmentOptionResponse(id=item.id, code=item.code, name=item.name, is_active=item.is_active)
            for item in department_result.scalars().all()
        ],
        roles=[
            RoleOptionResponse(id=item.id, name=item.name, is_active=item.is_active)
            for item in role_result.scalars().all()
        ],
    )


async def _load_user_by_id(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.department),
            selectinload(User.roles).selectinload(UserRole.role),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def _resolve_role_records(session: AsyncSession, role_names: list[str]) -> list[Role]:
    cleaned = sorted({name.strip() for name in role_names if name.strip()})
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one role is required")

    result = await session.execute(select(Role).where(Role.name.in_(cleaned)))
    roles = list(result.scalars().all())
    if len(roles) != len(cleaned):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more roles are invalid")
    return roles


async def _resolve_department_id(session: AsyncSession, department_id: int | None) -> int | None:
    if department_id is None:
        return None
    result = await session.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department is invalid")
    return department.id


async def create_user(session: AsyncSession, actor_user: User, payload: UserCreateRequest) -> UserAdminItemResponse:
    existing_username = await session.execute(select(User).where(User.username == payload.username))
    if existing_username.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already in use")

    existing_email = await session.execute(select(User).where(User.email == payload.email))
    if existing_email.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")

    _validate_superuser_assignment(role_names=payload.roles, is_superuser=payload.is_superuser)
    role_records = await _resolve_role_records(session, payload.roles)
    department_id = await _resolve_department_id(session, payload.department_id)

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
        department_id=department_id,
    )
    session.add(user)
    await session.flush()

    for role in role_records:
        session.add(UserRole(user_id=user.id, role_id=role.id))

    await write_audit_log(
        session,
        action="user.created",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor_user.id,
        target_user_id=user.id,
        details={
            "username": user.username,
            "email": user.email,
            "roles": payload.roles,
            "department_id": department_id,
            "is_active": payload.is_active,
            "is_superuser": payload.is_superuser,
        },
    )
    await session.commit()
    user = await _load_user_by_id(session, user.id)
    return _serialize_user_item(user)


async def update_user(session: AsyncSession, actor_user: User, user_id: int, payload: UserUpdateRequest) -> UserAdminItemResponse:
    user = await _load_user_by_id(session, user_id)
    changes = payload.model_dump(exclude_unset=True)
    target_roles = payload.roles if "roles" in changes and payload.roles is not None else [item.role.name for item in user.roles]
    target_superuser = payload.is_superuser if "is_superuser" in changes and payload.is_superuser is not None else user.is_superuser
    previous_is_active = user.is_active

    _validate_superuser_assignment(role_names=target_roles, is_superuser=target_superuser)

    if "email" in changes and payload.email is not None and payload.email != user.email:
        existing_email = await session.execute(select(User).where(User.email == payload.email))
        existing = existing_email.scalar_one_or_none()
        if existing is not None and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")
        user.email = payload.email

    if "full_name" in changes:
        user.full_name = payload.full_name

    if "department_id" in changes:
        user.department_id = await _resolve_department_id(session, payload.department_id)

    if "is_active" in changes:
        user.is_active = payload.is_active

    if "is_superuser" in changes:
        user.is_superuser = payload.is_superuser

    if "roles" in changes and payload.roles is not None:
        role_records = await _resolve_role_records(session, payload.roles)
        await session.execute(UserRole.__table__.delete().where(UserRole.user_id == user.id))
        for role in role_records:
            session.add(UserRole(user_id=user.id, role_id=role.id))

    audit_action = "user.updated"
    if "is_active" in changes:
        if previous_is_active and payload.is_active is False:
            audit_action = "user.deactivated"
        elif not previous_is_active and payload.is_active is True:
            audit_action = "user.activated"

    await write_audit_log(
        session,
        action=audit_action,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor_user.id,
        target_user_id=user.id,
        details={
            "changed_fields": sorted(changes.keys()),
            "roles": target_roles,
            "department_id": user.department_id,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        },
    )
    await session.commit()
    user = await _load_user_by_id(session, user.id)
    return _serialize_user_item(user)


async def reset_user_password(session: AsyncSession, actor_user: User, user_id: int, new_password: str) -> None:
    user = await _load_user_by_id(session, user_id)
    user.password_hash = hash_password(new_password)
    await write_audit_log(
        session,
        action="user.password_reset",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor_user.id,
        target_user_id=user.id,
        details={"username": user.username},
    )
    await session.commit()
