from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.db.models import Department, Role, User, UserRole
from app.db.session import AsyncSessionLocal

settings = get_settings()


async def get_or_create_department(session) -> Department:
    result = await session.execute(select(Department).where(Department.code == settings.seed_default_department_code))
    department = result.scalar_one_or_none()
    if department is not None:
        return department

    department = Department(
        code=settings.seed_default_department_code,
        name=settings.seed_default_department_name,
        description="Default department seeded for Repo B auth foundation.",
    )
    session.add(department)
    await session.flush()
    return department


async def get_or_create_role(session, name: str, description: str) -> Role:
    result = await session.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is not None:
        return role

    role = Role(name=name, description=description)
    session.add(role)
    await session.flush()
    return role


async def get_or_create_user(
    session,
    *,
    username: str,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool,
    department_id: int,
) -> User:
    result = await session.execute(select(User).where((User.username == username) | (User.email == email)))
    user = result.scalar_one_or_none()
    if user is not None:
        updated = False
        if user.department_id != department_id:
            user.department_id = department_id
            updated = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            updated = True
        if user.full_name != full_name:
            user.full_name = full_name
            updated = True
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            updated = True
        if updated:
            await session.flush()
        return user

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_superuser=is_superuser,
        department_id=department_id,
    )
    session.add(user)
    await session.flush()
    return user


async def ensure_user_role(session, *, user_id: int, role_id: int) -> None:
    result = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    mapping = result.scalar_one_or_none()
    if mapping is None:
        session.add(UserRole(user_id=user_id, role_id=role_id))
        await session.flush()


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        department = await get_or_create_department(session)

        admin_role = await get_or_create_role(session, "admin", "Administrative access to Repo B.")
        await get_or_create_role(session, "analyst", "Analyst access to alerts and workflow.")
        await get_or_create_role(session, "viewer", "Read-only access to Repo B.")

        admin_user = await get_or_create_user(
            session,
            username=settings.seed_admin_username,
            email=settings.seed_admin_email,
            password=settings.seed_admin_password,
            full_name=settings.seed_admin_full_name,
            is_superuser=False,
            department_id=department.id,
        )
        superadmin_user = await get_or_create_user(
            session,
            username=settings.seed_superadmin_username,
            email=settings.seed_superadmin_email,
            password=settings.seed_superadmin_password,
            full_name=settings.seed_superadmin_full_name,
            is_superuser=True,
            department_id=department.id,
        )

        await ensure_user_role(session, user_id=admin_user.id, role_id=admin_role.id)
        await ensure_user_role(session, user_id=superadmin_user.id, role_id=admin_role.id)

        await session.commit()

        print("Seed completed:")
        print(f"- department: {department.code} / {department.name}")
        print(f"- admin: {settings.seed_admin_username}")
        print(f"- superadmin: {settings.seed_superadmin_username}")


if __name__ == "__main__":
    asyncio.run(seed())
