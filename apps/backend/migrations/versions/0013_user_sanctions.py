"""
Create user_sanctions table for moderation bans/warnings and related constraints.

Revision ID: 0013
Revises: 0012
Create Date: 2025-09-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "user_sanctions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.Text(), nullable=False),  # ban|warning|mute|limit|shadowban
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'active'")
        ),  # active|canceled|expired
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("issued_by", sa.Text(), nullable=True),
        sa.Column(
            "issued_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "starts_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("meta", JSONB, nullable=True),
    )
    op.create_index("ix_user_sanctions_user", "user_sanctions", ["user_id"])
    op.create_index("ix_user_sanctions_type_status", "user_sanctions", ["type", "status"])


def downgrade() -> None:
    op.drop_index("ix_user_sanctions_type_status", table_name="user_sanctions")
    op.drop_index("ix_user_sanctions_user", table_name="user_sanctions")
    op.drop_table("user_sanctions")
