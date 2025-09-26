"""create broadcast tables

Revision ID: 0023
Revises: 0022
Create Date: 2025-09-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels = None
depends_on = None


_STATUS_ENUM_NAME = "notification_broadcast_status"
_AUDIENCE_ENUM_NAME = "notification_broadcast_audience_type"


_STATUS_VALUES = [
    "draft",
    "scheduled",
    "sending",
    "sent",
    "failed",
    "cancelled",
]
_AUDIENCE_VALUES = ["all_users", "segment", "explicit_users"]


def _ensure_enum(name: str, values: list[str]) -> None:
    bind = op.get_bind()
    enum_type = postgresql.ENUM(*values, name=name)
    enum_type.create(bind, checkfirst=True)


def _drop_enum(name: str) -> None:
    bind = op.get_bind()
    enum_type = postgresql.ENUM(name=name)
    enum_type.drop(bind, checkfirst=True)


def upgrade() -> None:
    _ensure_enum(_STATUS_ENUM_NAME, _STATUS_VALUES)
    _ensure_enum(_AUDIENCE_ENUM_NAME, _AUDIENCE_VALUES)

    status_enum = postgresql.ENUM(
        *_STATUS_VALUES,
        name=_STATUS_ENUM_NAME,
        create_type=False,
    )
    audience_enum = postgresql.ENUM(
        *_AUDIENCE_VALUES,
        name=_AUDIENCE_ENUM_NAME,
        create_type=False,
    )

    op.create_table(
        "notification_broadcasts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audience_type", audience_enum, nullable=False),
        sa.Column("audience_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("audience_user_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_index(
        "ix_notification_broadcasts_status",
        "notification_broadcasts",
        ["status"],
    )
    op.create_index(
        "ix_notification_broadcasts_created_at",
        "notification_broadcasts",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_broadcasts_created_at",
        table_name="notification_broadcasts",
    )
    op.drop_index(
        "ix_notification_broadcasts_status",
        table_name="notification_broadcasts",
    )
    op.drop_table("notification_broadcasts")

    _drop_enum(_STATUS_ENUM_NAME)
    _drop_enum(_AUDIENCE_ENUM_NAME)
