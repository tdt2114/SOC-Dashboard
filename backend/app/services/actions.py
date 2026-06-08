from __future__ import annotations

import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import UpstreamServiceError
from app.db.models import PendingAction, Role, User, UserRole
from app.schemas.actions import (
    ACTION_COMMANDS,
    PendingActionCreateRequest,
    PendingActionItemResponse,
    PendingActionListResponse,
)
from app.services.audit import write_audit_log
from app.services.notifications import create_notification
from app.services.wazuh_api import WazuhApiClient


APPROVAL_ROLES = {"admin"}
ACTIVE_STATUSES = {"pending", "approved", "rejected", "expired"}


def _serialize(item: PendingAction) -> PendingActionItemResponse:
    return PendingActionItemResponse(
        id=item.id,
        token=item.token,
        action_type=item.action_type,
        command=item.command,
        target_agent_id=item.target_agent_id,
        arguments=item.arguments,
        reason=item.reason,
        rule_id=item.rule_id,
        alert_id=item.alert_id,
        case_id=item.case_id,
        status=item.status,
        requested_by=item.requested_by,
        decided_by_user_id=item.decided_by_user_id,
        decided_by_username=item.decided_by_user.username if item.decided_by_user else None,
        decided_at=item.decided_at,
        execution_status=item.execution_status,
        execution_detail=item.execution_detail,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _load_by_token(session: AsyncSession, token: str) -> PendingAction:
    result = await session.execute(
        select(PendingAction)
        .where(PendingAction.token == token)
        .options(selectinload(PendingAction.decided_by_user))
        .execution_options(populate_existing=True)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending action not found")
    return item


async def _notify_approvers(session: AsyncSession, action: PendingAction) -> None:
    result = await session.execute(
        select(User.id)
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .outerjoin(Role, Role.id == UserRole.role_id)
        .where(User.is_active.is_(True), or_(User.is_superuser.is_(True), Role.name == "admin"))
        .distinct()
    )
    approver_ids = [row[0] for row in result.all()]
    for user_id in approver_ids:
        await create_notification(
            session,
            user_id=user_id,
            type="action.pending",
            title=f"Approval required: {action.action_type}",
            body=(
                f"SOAR requested '{action.action_type}' on agent {action.target_agent_id}. "
                f"{action.reason or 'No reason provided.'}"
            ),
            link_url=f"/cases/{action.case_id}" if action.case_id else None,
        )


async def create_pending_action(
    session: AsyncSession,
    payload: PendingActionCreateRequest,
    *,
    requested_by: str,
) -> PendingActionItemResponse:
    action_type = payload.action_type.strip().lower()
    command = ACTION_COMMANDS.get(action_type)
    if command is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported action_type. Allowed: {', '.join(sorted(ACTION_COMMANDS))}",
        )

    item = PendingAction(
        token=secrets.token_urlsafe(32),
        action_type=action_type,
        command=command,
        target_agent_id=payload.target_agent_id.strip(),
        arguments=payload.arguments,
        reason=(payload.reason.strip() if payload.reason else None),
        rule_id=(payload.rule_id.strip() if payload.rule_id else None),
        alert_id=(payload.alert_id.strip() if payload.alert_id else None),
        case_id=payload.case_id,
        status="pending",
        requested_by=(payload.requested_by.strip() if payload.requested_by else requested_by),
    )
    session.add(item)
    await session.flush()

    await _notify_approvers(session, item)
    await write_audit_log(
        session,
        action="action.requested",
        entity_type="pending_action",
        entity_id=item.id,
        actor_user_id=None,
        details={
            "action_type": item.action_type,
            "target_agent_id": item.target_agent_id,
            "requested_by": item.requested_by,
            "case_id": item.case_id,
        },
    )
    await session.commit()
    return _serialize(await _load_by_token(session, item.token))


async def list_pending_actions(
    session: AsyncSession,
    *,
    status_filter: str | None = None,
    case_id: int | None = None,
) -> PendingActionListResponse:
    query = select(PendingAction).options(selectinload(PendingAction.decided_by_user))
    if status_filter:
        normalized = status_filter.strip().lower()
        if normalized not in ACTIVE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
        query = query.where(PendingAction.status == normalized)
    if case_id is not None:
        query = query.where(PendingAction.case_id == case_id)
    query = query.order_by(PendingAction.created_at.desc())

    result = await session.execute(query)
    items = list(result.scalars().all())
    return PendingActionListResponse(items=[_serialize(item) for item in items], total=len(items))


async def get_pending_action(session: AsyncSession, token: str) -> PendingActionItemResponse:
    return _serialize(await _load_by_token(session, token))


async def _execute_active_response(action: PendingAction) -> tuple[str, str]:
    settings = get_settings()
    if not settings.wazuh_api_password:
        return "skipped", "Wazuh API password not configured; response not dispatched."
    client = WazuhApiClient(settings)
    try:
        response = await client.run_active_response(
            agent_id=action.target_agent_id,
            command=action.command,
            arguments=action.arguments,
        )
    except UpstreamServiceError as exc:
        return "failed", f"Wazuh API error: {exc}"
    message = response.get("message") if isinstance(response, dict) else None
    return "success", str(message or "Active response dispatched to Wazuh manager.")[:1000]


async def approve_pending_action(
    session: AsyncSession,
    actor_user: User,
    token: str,
) -> PendingActionItemResponse:
    item = await _load_by_token(session, token)
    if item.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Action already {item.status}; only pending actions can be approved.",
        )

    item.status = "approved"
    item.decided_by_user_id = actor_user.id
    item.decided_at = datetime.now(UTC)

    execution_status, execution_detail = await _execute_active_response(item)
    item.execution_status = execution_status
    item.execution_detail = execution_detail

    await write_audit_log(
        session,
        action="action.approved",
        entity_type="pending_action",
        entity_id=item.id,
        actor_user_id=actor_user.id,
        details={
            "action_type": item.action_type,
            "target_agent_id": item.target_agent_id,
            "execution_status": execution_status,
        },
    )
    await session.commit()
    return _serialize(await _load_by_token(session, token))


async def reject_pending_action(
    session: AsyncSession,
    actor_user: User,
    token: str,
    reason: str | None,
) -> PendingActionItemResponse:
    item = await _load_by_token(session, token)
    if item.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Action already {item.status}; only pending actions can be rejected.",
        )

    item.status = "rejected"
    item.decided_by_user_id = actor_user.id
    item.decided_at = datetime.now(UTC)
    item.execution_status = "skipped"
    cleaned_reason = reason.strip() if reason else None
    item.execution_detail = f"Rejected by {actor_user.username}" + (f": {cleaned_reason}" if cleaned_reason else "")

    await write_audit_log(
        session,
        action="action.rejected",
        entity_type="pending_action",
        entity_id=item.id,
        actor_user_id=actor_user.id,
        details={"action_type": item.action_type, "reason": cleaned_reason},
    )
    await session.commit()
    return _serialize(await _load_by_token(session, token))
