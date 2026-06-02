from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Case, CaseAlert, CaseComment, User
from app.schemas.cases import (
    CaseAlertCreateRequest,
    CaseAlertItemResponse,
    CaseCommentCreateRequest,
    CaseCommentItemResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseItemResponse,
    CaseListResponse,
    CaseUpdateRequest,
)
from app.services.audit import write_audit_log


CASE_STATUSES = {"open", "investigating", "closed"}
CASE_SEVERITIES = {"low", "medium", "high", "critical"}


def _clean_text(value: str, *, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} is required")
    return cleaned


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_status(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in CASE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid case status")
    return cleaned


def _clean_severity(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in CASE_SEVERITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid case severity")
    return cleaned


def _serialize_case(item: Case) -> CaseItemResponse:
    return CaseItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        status=item.status,
        severity=item.severity,
        owner_user_id=item.owner_user_id,
        owner_username=item.owner_user.username if item.owner_user else None,
        owner_full_name=item.owner_user.full_name if item.owner_user else None,
        created_by_user_id=item.created_by_user_id,
        created_by_username=item.created_by_user.username if item.created_by_user else None,
        alert_count=len(item.alerts),
        comment_count=len(item.comments),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_case_detail(item: Case) -> CaseDetailResponse:
    base = _serialize_case(item).model_dump()
    return CaseDetailResponse(
        **base,
        alerts=[
            CaseAlertItemResponse(id=alert.id, alert_id=alert.alert_id, created_at=alert.created_at)
            for alert in sorted(item.alerts, key=lambda case_alert: case_alert.created_at, reverse=True)
        ],
        comments=[
            CaseCommentItemResponse(
                id=comment.id,
                author_user_id=comment.author_user_id,
                author_username=comment.author_user.username,
                author_full_name=comment.author_user.full_name,
                body=comment.body,
                created_at=comment.created_at,
            )
            for comment in sorted(item.comments, key=lambda case_comment: case_comment.created_at)
        ],
    )


async def _resolve_owner(session: AsyncSession, owner_user_id: int | None) -> User | None:
    if owner_user_id is None:
        return None
    result = await session.execute(select(User).where(User.id == owner_user_id, User.is_active.is_(True)))
    owner = result.scalar_one_or_none()
    if owner is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Case owner is invalid")
    return owner


async def _load_case(session: AsyncSession, case_id: int) -> Case:
    result = await session.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.owner_user),
            selectinload(Case.created_by_user),
            selectinload(Case.alerts),
            selectinload(Case.comments).selectinload(CaseComment.author_user),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return item


async def list_cases(session: AsyncSession) -> CaseListResponse:
    result = await session.execute(
        select(Case)
        .options(
            selectinload(Case.owner_user),
            selectinload(Case.created_by_user),
            selectinload(Case.alerts),
            selectinload(Case.comments),
        )
        .order_by(Case.updated_at.desc())
    )
    items = list(result.scalars().all())
    return CaseListResponse(items=[_serialize_case(item) for item in items], total=len(items))


async def create_case(session: AsyncSession, actor_user: User, payload: CaseCreateRequest) -> CaseDetailResponse:
    owner = await _resolve_owner(session, payload.owner_user_id)
    item = Case(
        title=_clean_text(payload.title, field_name="Case title"),
        description=_clean_optional_text(payload.description),
        status=_clean_status(payload.status),
        severity=_clean_severity(payload.severity),
        owner_user_id=owner.id if owner else actor_user.id,
        created_by_user_id=actor_user.id,
    )
    session.add(item)
    await session.flush()

    if payload.alert_id:
        session.add(CaseAlert(case_id=item.id, alert_id=payload.alert_id.strip(), added_by_user_id=actor_user.id))

    await write_audit_log(
        session,
        action="case.created",
        entity_type="case",
        entity_id=item.id,
        actor_user_id=actor_user.id,
        target_user_id=item.owner_user_id,
        details={"title": item.title, "status": item.status, "severity": item.severity, "alert_id": payload.alert_id},
    )
    await session.commit()
    return _serialize_case_detail(await _load_case(session, item.id))


async def get_case(session: AsyncSession, case_id: int) -> CaseDetailResponse:
    return _serialize_case_detail(await _load_case(session, case_id))


async def update_case(
    session: AsyncSession,
    actor_user: User,
    case_id: int,
    payload: CaseUpdateRequest,
) -> CaseDetailResponse:
    item = await _load_case(session, case_id)
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes and payload.title is not None:
        item.title = _clean_text(payload.title, field_name="Case title")
    if "description" in changes:
        item.description = _clean_optional_text(payload.description)
    if "status" in changes and payload.status is not None:
        item.status = _clean_status(payload.status)
    if "severity" in changes and payload.severity is not None:
        item.severity = _clean_severity(payload.severity)
    if "owner_user_id" in changes:
        owner = await _resolve_owner(session, payload.owner_user_id)
        item.owner_user_id = owner.id if owner else None

    await write_audit_log(
        session,
        action="case.updated",
        entity_type="case",
        entity_id=item.id,
        actor_user_id=actor_user.id,
        target_user_id=item.owner_user_id,
        details={"changed_fields": sorted(changes.keys())},
    )
    await session.commit()
    return _serialize_case_detail(await _load_case(session, item.id))


async def add_case_alert(
    session: AsyncSession,
    actor_user: User,
    case_id: int,
    payload: CaseAlertCreateRequest,
) -> CaseDetailResponse:
    item = await _load_case(session, case_id)
    alert_id = payload.alert_id.strip()
    exists = await session.execute(select(CaseAlert).where(CaseAlert.case_id == item.id, CaseAlert.alert_id == alert_id))
    if exists.scalar_one_or_none() is None:
        session.add(CaseAlert(case_id=item.id, alert_id=alert_id, added_by_user_id=actor_user.id))
        item.updated_at = datetime.now(UTC)
        await write_audit_log(
            session,
            action="case.alert_added",
            entity_type="case",
            entity_id=item.id,
            actor_user_id=actor_user.id,
            target_user_id=item.owner_user_id,
            details={"alert_id": alert_id},
        )
        await session.commit()
    return _serialize_case_detail(await _load_case(session, item.id))


async def remove_case_alert(session: AsyncSession, actor_user: User, case_id: int, alert_id: str) -> CaseDetailResponse:
    item = await _load_case(session, case_id)
    result = await session.execute(select(CaseAlert).where(CaseAlert.case_id == item.id, CaseAlert.alert_id == alert_id))
    case_alert = result.scalar_one_or_none()
    if case_alert is not None:
        await session.delete(case_alert)
        item.updated_at = datetime.now(UTC)
        await write_audit_log(
            session,
            action="case.alert_removed",
            entity_type="case",
            entity_id=item.id,
            actor_user_id=actor_user.id,
            target_user_id=item.owner_user_id,
            details={"alert_id": alert_id},
        )
        await session.commit()
    return _serialize_case_detail(await _load_case(session, item.id))


async def add_case_comment(
    session: AsyncSession,
    actor_user: User,
    case_id: int,
    payload: CaseCommentCreateRequest,
) -> CaseDetailResponse:
    item = await _load_case(session, case_id)
    body = _clean_text(payload.body, field_name="Comment")
    comment = CaseComment(case_id=item.id, author_user_id=actor_user.id, body=body)
    session.add(comment)
    item.updated_at = datetime.now(UTC)
    await session.flush()
    await write_audit_log(
        session,
        action="case.comment_added",
        entity_type="case",
        entity_id=item.id,
        actor_user_id=actor_user.id,
        target_user_id=item.owner_user_id,
        details={"comment_id": comment.id},
    )
    await session.commit()
    return _serialize_case_detail(await _load_case(session, item.id))
