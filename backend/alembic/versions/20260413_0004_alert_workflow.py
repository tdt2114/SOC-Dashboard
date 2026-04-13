"""add alert workflow tables

Revision ID: 20260413_0004
Revises: 20260411_0003
Create Date: 2026-04-13 10:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0004"
down_revision = "20260411_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.String(length=255), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], name=op.f("fk_alert_assignments_assigned_by_user_id_users")),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], name=op.f("fk_alert_assignments_assigned_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_assignments")),
        sa.UniqueConstraint("alert_id", name=op.f("uq_alert_assignments_alert_id")),
    )
    op.create_index(op.f("ix_alert_assignments_alert_id"), "alert_assignments", ["alert_id"], unique=True)

    op.create_table(
        "alert_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.String(length=255), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], name=op.f("fk_alert_notes_author_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_notes")),
    )
    op.create_index(op.f("ix_alert_notes_alert_id"), "alert_notes", ["alert_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_notes_alert_id"), table_name="alert_notes")
    op.drop_table("alert_notes")
    op.drop_index(op.f("ix_alert_assignments_alert_id"), table_name="alert_assignments")
    op.drop_table("alert_assignments")
