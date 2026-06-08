"""add ai_analyses (AI SOC analyst cache)

Revision ID: 20260608_0010
Revises: 20260608_0009
Create Date: 2026-06-08 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260608_0010"
down_revision = "20260608_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_ref", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("attacker_intent", sa.Text(), nullable=True),
        sa.Column("mitre", sa.JSON(), nullable=True),
        sa.Column("recommended_action", sa.String(length=50), nullable=True),
        sa.Column("should_block", sa.Boolean(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name=op.f("fk_ai_analyses_created_by_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_analyses")),
        sa.UniqueConstraint("entity_type", "entity_ref", name="uq_ai_analyses_entity_type_entity_ref"),
    )
    op.create_index(op.f("ix_ai_analyses_entity_type"), "ai_analyses", ["entity_type"], unique=False)
    op.create_index(op.f("ix_ai_analyses_entity_ref"), "ai_analyses", ["entity_ref"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_analyses_entity_ref"), table_name="ai_analyses")
    op.drop_index(op.f("ix_ai_analyses_entity_type"), table_name="ai_analyses")
    op.drop_table("ai_analyses")
