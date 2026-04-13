"""add refresh tokens

Revision ID: 20260411_0002
Revises: 20260411_0001
Create Date: 2026-04-11 15:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260411_0002"
down_revision = "20260411_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_id", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_refresh_tokens_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
    )
    op.create_index(op.f("ix_refresh_tokens_token_id"), "refresh_tokens", ["token_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_token_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
