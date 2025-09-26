"""notification inbox stage1 payloads

Revision ID: 0020
Revises: 0019
Create Date: 2025-09-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("topic_key", sa.Text(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("channel_key", sa.Text(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("event_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "priority",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("cta_label", sa.Text(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("cta_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "meta",
            pg.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_notifications_topic",
        "notifications",
        ["topic_key"],
        unique=False,
        postgresql_where=sa.text("topic_key IS NOT NULL"),
    )
    op.create_index(
        "ix_notifications_channel",
        "notifications",
        ["channel_key"],
        unique=False,
        postgresql_where=sa.text("channel_key IS NOT NULL"),
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("read_at IS NULL"),
    )
    op.create_index(
        "ux_notifications_event_id",
        "notifications",
        ["event_id"],
        unique=True,
        postgresql_where=sa.text("event_id IS NOT NULL"),
    )

    op.execute(
        sa.text(
            """
            UPDATE notifications
            SET updated_at = created_at
            WHERE updated_at IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ux_notifications_event_id", table_name="notifications")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_index("ix_notifications_channel", table_name="notifications")
    op.drop_index("ix_notifications_topic", table_name="notifications")
    op.drop_column("notifications", "updated_at")
    op.drop_column("notifications", "meta")
    op.drop_column("notifications", "cta_url")
    op.drop_column("notifications", "cta_label")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "event_id")
    op.drop_column("notifications", "channel_key")
    op.drop_column("notifications", "topic_key")
