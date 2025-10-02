"""Create platform moderation snapshot table.

Revision ID: 0104_platform_moderation_state
Revises: 0103_nodes_moderation
Create Date: 2025-10-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0104_platform_moderation_state"
down_revision = "0103_nodes_moderation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_moderation_state",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "payload",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute(
        "INSERT INTO platform_moderation_state (id, payload) VALUES ('singleton', '{}'::jsonb)"
        " ON CONFLICT (id) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("platform_moderation_state")
