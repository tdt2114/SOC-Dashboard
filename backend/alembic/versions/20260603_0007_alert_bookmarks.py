"""add alert bookmarks

Revision ID: 20260603_0007
Revises: 20260603_0006
Create Date: 2026-06-03 01:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260603_0007"
down_revision = "20260603_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_alert_bookmarks_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_bookmarks")),
        sa.UniqueConstraint("user_id", "alert_id", name="uq_alert_bookmarks_user_id_alert_id"),
    )
    op.create_index(op.f("ix_alert_bookmarks_alert_id"), "alert_bookmarks", ["alert_id"], unique=False)
    op.create_index(op.f("ix_alert_bookmarks_user_id"), "alert_bookmarks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_bookmarks_user_id"), table_name="alert_bookmarks")
    op.drop_index(op.f("ix_alert_bookmarks_alert_id"), table_name="alert_bookmarks")
    op.drop_table("alert_bookmarks")
