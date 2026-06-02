from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AlertBookmark, User
from app.schemas.alert_bookmarks import AlertBookmarkResponse
from app.services.audit import write_audit_log


def _serialize_bookmark(alert_id: str, item: AlertBookmark | None) -> AlertBookmarkResponse:
    return AlertBookmarkResponse(
        alert_id=alert_id,
        is_bookmarked=item is not None,
        bookmark_id=item.id if item else None,
        created_at=item.created_at if item else None,
    )


async def _load_bookmark(session: AsyncSession, user: User, alert_id: str) -> AlertBookmark | None:
    result = await session.execute(
        select(AlertBookmark).where(AlertBookmark.user_id == user.id, AlertBookmark.alert_id == alert_id)
    )
    return result.scalar_one_or_none()


async def get_alert_bookmark(session: AsyncSession, user: User, alert_id: str) -> AlertBookmarkResponse:
    item = await _load_bookmark(session, user, alert_id)
    return _serialize_bookmark(alert_id, item)


async def bookmark_alert(session: AsyncSession, user: User, alert_id: str) -> AlertBookmarkResponse:
    item = await _load_bookmark(session, user, alert_id)
    if item is None:
        item = AlertBookmark(user_id=user.id, alert_id=alert_id)
        session.add(item)
        await session.flush()
        await write_audit_log(
            session,
            action="alert.bookmarked",
            entity_type="alert",
            entity_id=None,
            actor_user_id=user.id,
            target_user_id=user.id,
            details={"alert_id": alert_id, "bookmark_id": item.id},
        )
        await session.commit()
        await session.refresh(item)
    return _serialize_bookmark(alert_id, item)


async def unbookmark_alert(session: AsyncSession, user: User, alert_id: str) -> AlertBookmarkResponse:
    item = await _load_bookmark(session, user, alert_id)
    if item is not None:
        details = {"alert_id": alert_id, "bookmark_id": item.id}
        await session.delete(item)
        await write_audit_log(
            session,
            action="alert.unbookmarked",
            entity_type="alert",
            entity_id=None,
            actor_user_id=user.id,
            target_user_id=user.id,
            details=details,
        )
        await session.commit()
    return _serialize_bookmark(alert_id, None)
