"""add cases

Revision ID: 20260603_0008
Revises: 20260603_0007
Create Date: 2026-06-03 02:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260603_0008"
down_revision = "20260603_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_cases_created_by_user_id_users")),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name=op.f("fk_cases_owner_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cases")),
    )
    op.create_index(op.f("ix_cases_severity"), "cases", ["severity"], unique=False)
    op.create_index(op.f("ix_cases_status"), "cases", ["status"], unique=False)

    op.create_table(
        "case_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.String(length=255), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["added_by_user_id"], ["users.id"], name=op.f("fk_case_alerts_added_by_user_id_users")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_alerts_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_alerts")),
        sa.UniqueConstraint("case_id", "alert_id", name="uq_case_alerts_case_id_alert_id"),
    )
    op.create_index(op.f("ix_case_alerts_alert_id"), "case_alerts", ["alert_id"], unique=False)
    op.create_index(op.f("ix_case_alerts_case_id"), "case_alerts", ["case_id"], unique=False)

    op.create_table(
        "case_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], name=op.f("fk_case_comments_author_user_id_users")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_case_comments_case_id_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_comments")),
    )
    op.create_index(op.f("ix_case_comments_case_id"), "case_comments", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_comments_case_id"), table_name="case_comments")
    op.drop_table("case_comments")
    op.drop_index(op.f("ix_case_alerts_case_id"), table_name="case_alerts")
    op.drop_index(op.f("ix_case_alerts_alert_id"), table_name="case_alerts")
    op.drop_table("case_alerts")
    op.drop_index(op.f("ix_cases_status"), table_name="cases")
    op.drop_index(op.f("ix_cases_severity"), table_name="cases")
    op.drop_table("cases")
