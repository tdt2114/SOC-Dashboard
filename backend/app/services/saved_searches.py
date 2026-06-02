from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SavedSearch, User
from app.schemas.saved_searches import (
    SavedSearchCreateRequest,
    SavedSearchItemResponse,
    SavedSearchListResponse,
    SavedSearchUpdateRequest,
)
from app.services.audit import write_audit_log


ALLOWED_FILTER_KEYS = {"q", "severity", "agent_name", "agent_id", "rule_id", "time_range"}


def _serialize_saved_search(item: SavedSearch) -> SavedSearchItemResponse:
    return SavedSearchItemResponse(
        id=item.id,
        name=item.name,
        filters=item.filters,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _clean_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Saved search name is required")
    return cleaned


def _clean_filters(filters: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in filters.items():
        if key not in ALLOWED_FILTER_KEYS or value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            cleaned[key] = normalized
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one alert filter is required")
    return cleaned


async def _get_owned_saved_search(session: AsyncSession, user: User, saved_search_id: int) -> SavedSearch:
    result = await session.execute(
        select(SavedSearch).where(SavedSearch.id == saved_search_id, SavedSearch.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    return item


async def _ensure_unique_name(
    session: AsyncSession,
    user: User,
    name: str,
    *,
    ignore_id: int | None = None,
) -> None:
    query = select(SavedSearch).where(SavedSearch.user_id == user.id, SavedSearch.name == name)
    if ignore_id is not None:
        query = query.where(SavedSearch.id != ignore_id)
    result = await session.execute(query)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Saved search name is already in use")


async def list_saved_searches(session: AsyncSession, user: User) -> SavedSearchListResponse:
    result = await session.execute(
        select(SavedSearch).where(SavedSearch.user_id == user.id).order_by(SavedSearch.updated_at.desc())
    )
    items = list(result.scalars().all())
    return SavedSearchListResponse(items=[_serialize_saved_search(item) for item in items], total=len(items))


async def create_saved_search(
    session: AsyncSession,
    user: User,
    payload: SavedSearchCreateRequest,
) -> SavedSearchItemResponse:
    name = _clean_name(payload.name)
    filters = _clean_filters(payload.filters)
    await _ensure_unique_name(session, user, name)

    item = SavedSearch(user_id=user.id, name=name, filters=filters)
    session.add(item)
    await session.flush()
    await write_audit_log(
        session,
        action="saved_search.created",
        entity_type="saved_search",
        entity_id=item.id,
        actor_user_id=user.id,
        target_user_id=user.id,
        details={"name": name, "filters": filters},
    )
    await session.commit()
    await session.refresh(item)
    return _serialize_saved_search(item)


async def update_saved_search(
    session: AsyncSession,
    user: User,
    saved_search_id: int,
    payload: SavedSearchUpdateRequest,
) -> SavedSearchItemResponse:
    item = await _get_owned_saved_search(session, user, saved_search_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _serialize_saved_search(item)

    if "name" in changes and payload.name is not None:
        name = _clean_name(payload.name)
        await _ensure_unique_name(session, user, name, ignore_id=item.id)
        item.name = name
    if "filters" in changes and payload.filters is not None:
        item.filters = _clean_filters(payload.filters)

    await write_audit_log(
        session,
        action="saved_search.updated",
        entity_type="saved_search",
        entity_id=item.id,
        actor_user_id=user.id,
        target_user_id=user.id,
        details={"changed_fields": sorted(changes.keys()), "name": item.name, "filters": item.filters},
    )
    await session.commit()
    await session.refresh(item)
    return _serialize_saved_search(item)


async def delete_saved_search(session: AsyncSession, user: User, saved_search_id: int) -> None:
    item = await _get_owned_saved_search(session, user, saved_search_id)
    details = {"name": item.name, "filters": item.filters}
    await session.delete(item)
    await write_audit_log(
        session,
        action="saved_search.deleted",
        entity_type="saved_search",
        entity_id=saved_search_id,
        actor_user_id=user.id,
        target_user_id=user.id,
        details=details,
    )
    await session.commit()
