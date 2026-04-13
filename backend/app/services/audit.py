from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    details: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            details=details,
        )
    )
    await session.flush()
