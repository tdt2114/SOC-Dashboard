from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, User
from app.schemas.notifications import NotificationItemResponse, NotificationListResponse


def _serialize_notification(item: Notification) -> NotificationItemResponse:
    return NotificationItemResponse(
        id=item.id,
        type=item.type,
        title=item.title,
        body=item.body,
        link_url=item.link_url,
        is_read=item.is_read,
        created_at=item.created_at,
        read_at=item.read_at,
    )


async def create_notification(
    session: AsyncSession,
    *,
    user_id: int,
    type: str,
    title: str,
    body: str,
    link_url: str | None = None,
) -> None:
    session.add(
        Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            link_url=link_url,
            is_read=False,
        )
    )
    await session.flush()


async def list_notifications(session: AsyncSession, current_user: User) -> NotificationListResponse:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    items = list(result.scalars().all())

    unread_result = await session.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    unread_count = int(unread_result.scalar_one() or 0)

    return NotificationListResponse(
        items=[_serialize_notification(item) for item in items],
        unread_count=unread_count,
    )


async def mark_notification_read(session: AsyncSession, current_user: User, notification_id: int) -> None:
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    item.is_read = True
    item.read_at = datetime.now(UTC)
    await session.commit()


async def mark_all_notifications_read(session: AsyncSession, current_user: User) -> None:
    result = await session.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    now = datetime.now(UTC)
    for item in result.scalars().all():
        item.is_read = True
        item.read_at = now
    await session.commit()
