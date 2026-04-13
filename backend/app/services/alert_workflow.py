from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AlertAssignment, AlertNote, Role, User, UserRole
from app.schemas.alert_workflow import (
    AlertAssignmentInfo,
    AlertAssignmentRequest,
    AlertNoteCreateRequest,
    AlertNoteInfo,
    AlertWorkflowResponse,
    AlertWorkflowUserOption,
)
from app.services.auth import WORKFLOW_ROLES
from app.services.audit import write_audit_log
from app.services.notifications import create_notification


def _serialize_note(note: AlertNote) -> AlertNoteInfo:
    return AlertNoteInfo(
        id=note.id,
        author_user_id=note.author_user_id,
        author_username=note.author_user.username,
        author_full_name=note.author_user.full_name,
        body=note.body,
        created_at=note.created_at,
    )


async def _load_assignment(session: AsyncSession, alert_id: str) -> AlertAssignment | None:
    result = await session.execute(
        select(AlertAssignment)
        .where(AlertAssignment.alert_id == alert_id)
        .options(selectinload(AlertAssignment.assigned_user))
    )
    return result.scalar_one_or_none()


async def _load_active_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .outerjoin(Role, Role.id == UserRole.role_id)
        .where(
            User.is_active.is_(True),
            or_(
                User.is_superuser.is_(True),
                Role.name.in_(tuple(WORKFLOW_ROLES)),
            ),
        )
        .order_by(User.username.asc())
        .options(selectinload(User.roles).selectinload(UserRole.role))
    )
    return list(result.scalars().unique().all())


async def _load_notes(session: AsyncSession, alert_id: str) -> list[AlertNote]:
    result = await session.execute(
        select(AlertNote)
        .where(AlertNote.alert_id == alert_id)
        .order_by(AlertNote.created_at.desc())
        .options(selectinload(AlertNote.author_user))
    )
    return list(result.scalars().all())


async def get_alert_workflow(session: AsyncSession, alert_id: str) -> AlertWorkflowResponse:
    assignment = await _load_assignment(session, alert_id)
    notes = await _load_notes(session, alert_id)
    users = await _load_active_users(session)

    return AlertWorkflowResponse(
        alert_id=alert_id,
        assignee=AlertAssignmentInfo(
            user_id=assignment.assigned_user_id if assignment else None,
            username=assignment.assigned_user.username if assignment and assignment.assigned_user else None,
            full_name=assignment.assigned_user.full_name if assignment and assignment.assigned_user else None,
            updated_at=assignment.updated_at if assignment else None,
        ),
        assignee_options=[
            AlertWorkflowUserOption(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
            )
            for user in users
        ],
        notes=[_serialize_note(note) for note in notes],
    )


async def assign_alert(
    session: AsyncSession,
    *,
    alert_id: str,
    actor_user: User,
    payload: AlertAssignmentRequest,
) -> AlertWorkflowResponse:
    assignment = await _load_assignment(session, alert_id)
    assigned_user: User | None = None
    if payload.assigned_user_id is not None:
        result = await session.execute(
            select(User)
            .outerjoin(UserRole, UserRole.user_id == User.id)
            .outerjoin(Role, Role.id == UserRole.role_id)
            .where(
                User.id == payload.assigned_user_id,
                User.is_active.is_(True),
                or_(
                    User.is_superuser.is_(True),
                    Role.name.in_(tuple(WORKFLOW_ROLES)),
                ),
            )
            .options(selectinload(User.roles).selectinload(UserRole.role))
        )
        assigned_user = result.scalars().unique().one_or_none()
        if assigned_user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user is invalid")

    if assignment is None:
        assignment = AlertAssignment(
            alert_id=alert_id,
            assigned_user_id=assigned_user.id if assigned_user else None,
            assigned_by_user_id=actor_user.id,
        )
        session.add(assignment)
        await session.flush()
    else:
        assignment.assigned_user_id = assigned_user.id if assigned_user else None
        assignment.assigned_by_user_id = actor_user.id

    await write_audit_log(
        session,
        action="alert.assigned" if assigned_user else "alert.unassigned",
        entity_type="alert",
        entity_id=None,
        actor_user_id=actor_user.id,
        target_user_id=assigned_user.id if assigned_user else None,
        details={
            "alert_id": alert_id,
            "assigned_user_id": assigned_user.id if assigned_user else None,
            "assigned_username": assigned_user.username if assigned_user else None,
        },
    )
    if assigned_user is not None:
        await create_notification(
            session,
            user_id=assigned_user.id,
            type="alert.assigned",
            title="New alert assignment",
            body=f"Alert {alert_id} was assigned to you by {actor_user.username}.",
            link_url=f"/alerts/{alert_id}",
        )
    await session.commit()
    return await get_alert_workflow(session, alert_id)


async def add_alert_note(
    session: AsyncSession,
    *,
    alert_id: str,
    actor_user: User,
    payload: AlertNoteCreateRequest,
) -> AlertWorkflowResponse:
    note_body = payload.body.strip()
    if not note_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note body cannot be empty")

    note = AlertNote(
        alert_id=alert_id,
        author_user_id=actor_user.id,
        body=note_body,
    )
    session.add(note)
    await session.flush()
    await write_audit_log(
        session,
        action="alert.note_added",
        entity_type="alert",
        entity_id=None,
        actor_user_id=actor_user.id,
        target_user_id=actor_user.id,
        details={
            "alert_id": alert_id,
            "note_id": note.id,
        },
    )
    await session.commit()
    return await get_alert_workflow(session, alert_id)
