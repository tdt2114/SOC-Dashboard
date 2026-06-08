"""add pending_actions (SOAR approval workflow)

Revision ID: 20260608_0009
Revises: 20260603_0008
Create Date: 2026-06-08 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260608_0009"
down_revision = "20260603_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("command", sa.String(length=100), nullable=False),
        sa.Column("target_agent_id", sa.String(length=50), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("rule_id", sa.String(length=50), nullable=True),
        sa.Column("alert_id", sa.String(length=255), nullable=True),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_by", sa.String(length=100), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_status", sa.String(length=20), nullable=True),
        sa.Column("execution_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_pending_actions_case_id_cases")),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"], ["users.id"], name=op.f("fk_pending_actions_decided_by_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pending_actions")),
    )
    op.create_index(op.f("ix_pending_actions_token"), "pending_actions", ["token"], unique=True)
    op.create_index(op.f("ix_pending_actions_action_type"), "pending_actions", ["action_type"], unique=False)
    op.create_index(op.f("ix_pending_actions_target_agent_id"), "pending_actions", ["target_agent_id"], unique=False)
    op.create_index(op.f("ix_pending_actions_case_id"), "pending_actions", ["case_id"], unique=False)
    op.create_index(op.f("ix_pending_actions_status"), "pending_actions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pending_actions_status"), table_name="pending_actions")
    op.drop_index(op.f("ix_pending_actions_case_id"), table_name="pending_actions")
    op.drop_index(op.f("ix_pending_actions_target_agent_id"), table_name="pending_actions")
    op.drop_index(op.f("ix_pending_actions_action_type"), table_name="pending_actions")
    op.drop_index(op.f("ix_pending_actions_token"), table_name="pending_actions")
    op.drop_table("pending_actions")
