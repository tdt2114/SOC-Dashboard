from __future__ import annotations

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.models import AuditLog, User
from app.schemas.audit import AuditLogItemResponse, AuditLogListResponse


async def list_audit_logs(
    session: AsyncSession,
    *,
    action: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AuditLogListResponse:
    actor_user = aliased(User)
    target_user = aliased(User)

    filters = []
    if action:
        filters.append(AuditLog.action == action)

    if q:
        like_value = f"%{q}%"
        filters.append(
            or_(
                AuditLog.action.ilike(like_value),
                AuditLog.entity_type.ilike(like_value),
                actor_user.username.ilike(like_value),
                target_user.username.ilike(like_value),
            )
        )

    base_query = (
        select(
            AuditLog,
            actor_user.username.label("actor_username"),
            target_user.username.label("target_username"),
        )
        .outerjoin(actor_user, AuditLog.actor_user_id == actor_user.id)
        .outerjoin(target_user, AuditLog.target_user_id == target_user.id)
    )

    count_query = select(func.count()).select_from(AuditLog)
    if filters:
        base_query = base_query.where(*filters)
        count_query = (
            count_query
            .outerjoin(actor_user, AuditLog.actor_user_id == actor_user.id)
            .outerjoin(target_user, AuditLog.target_user_id == target_user.id)
            .where(*filters)
        )

    result = await session.execute(
        base_query
        .order_by(desc(AuditLog.created_at), desc(AuditLog.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    return AuditLogListResponse(
        items=[
            AuditLogItemResponse(
                id=row.AuditLog.id,
                action=row.AuditLog.action,
                entity_type=row.AuditLog.entity_type,
                entity_id=row.AuditLog.entity_id,
                actor_user_id=row.AuditLog.actor_user_id,
                actor_username=row.actor_username,
                target_user_id=row.AuditLog.target_user_id,
                target_username=row.target_username,
                details=row.AuditLog.details,
                created_at=row.AuditLog.created_at,
            )
            for row in rows
        ],
        total=total,
    )
