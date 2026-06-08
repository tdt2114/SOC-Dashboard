from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="department")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)

    department: Mapped[Department | None] = relationship(back_populates="users")
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alert_assignments: Mapped[list["AlertAssignment"]] = relationship(
        back_populates="assigned_user",
        cascade="all, delete-orphan",
        foreign_keys="AlertAssignment.assigned_user_id",
    )
    alert_notes: Mapped[list["AlertNote"]] = relationship(
        back_populates="author_user",
        cascade="all, delete-orphan",
        foreign_keys="AlertNote.author_user_id",
    )
    alert_bookmarks: Mapped[list["AlertBookmark"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AlertBookmark.user_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Notification.user_id",
    )
    saved_searches: Mapped[list["SavedSearch"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="SavedSearch.user_id",
    )
    owned_cases: Mapped[list["Case"]] = relationship(
        back_populates="owner_user",
        foreign_keys="Case.owner_user_id",
    )
    created_cases: Mapped[list["Case"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Case.created_by_user_id",
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship(back_populates="users")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AlertAssignment(TimestampMixin, Base):
    __tablename__ = "alert_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    assigned_user: Mapped[User | None] = relationship(
        back_populates="alert_assignments",
        foreign_keys=[assigned_user_id],
    )


class AlertNote(TimestampMixin, Base):
    __tablename__ = "alert_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    author_user: Mapped[User] = relationship(
        back_populates="alert_notes",
        foreign_keys=[author_user_id],
    )


class AlertBookmark(TimestampMixin, Base):
    __tablename__ = "alert_bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "alert_id", name="uq_alert_bookmarks_user_id_alert_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    user: Mapped[User] = relationship(
        back_populates="alert_bookmarks",
        foreign_keys=[user_id],
    )


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(
        back_populates="notifications",
        foreign_keys=[user_id],
    )


class SavedSearch(TimestampMixin, Base):
    __tablename__ = "saved_searches"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_saved_searches_user_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped[User] = relationship(
        back_populates="saved_searches",
        foreign_keys=[user_id],
    )


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="medium", nullable=False, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner_user: Mapped[User | None] = relationship(
        back_populates="owned_cases",
        foreign_keys=[owner_user_id],
    )
    created_by_user: Mapped[User | None] = relationship(
        back_populates="created_cases",
        foreign_keys=[created_by_user_id],
    )
    alerts: Mapped[list["CaseAlert"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    comments: Mapped[list["CaseComment"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseAlert(TimestampMixin, Base):
    __tablename__ = "case_alerts"
    __table_args__ = (
        UniqueConstraint("case_id", "alert_id", name="uq_case_alerts_case_id_alert_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    alert_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    added_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    case: Mapped[Case] = relationship(back_populates="alerts")


class CaseComment(TimestampMixin, Base):
    __tablename__ = "case_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    case: Mapped[Case] = relationship(back_populates="comments")
    author_user: Mapped[User] = relationship(foreign_keys=[author_user_id])


class PendingAction(TimestampMixin, Base):
    """A response action requested by SOAR that waits for human (admin) approval."""

    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    command: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    arguments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alert_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    decided_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    execution_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    decided_by_user: Mapped[User | None] = relationship(foreign_keys=[decided_by_user_id])
    case: Mapped[Case | None] = relationship(foreign_keys=[case_id])


class AiAnalysis(TimestampMixin, Base):
    """Cached AI triage for an alert/case/pending action (advisory only)."""

    __tablename__ = "ai_analyses"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_ref", name="uq_ai_analyses_entity_type_entity_ref"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    attacker_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitre: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    should_block: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by_user_id])


__all__ = [
    "Base",
    "AiAnalysis",
    "AlertAssignment",
    "AlertBookmark",
    "AlertNote",
    "AuditLog",
    "Case",
    "CaseAlert",
    "CaseComment",
    "Department",
    "Notification",
    "PendingAction",
    "Role",
    "RefreshToken",
    "SavedSearch",
    "User",
    "UserRole",
]
