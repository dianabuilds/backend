"""Create notification_config table for retention settings.

Revision ID: 0115_notifications_retention_config
Revises: 0114_notifications_schema
Create Date: 2025-10-27 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "0115_notifications_retention_config"
down_revision = "0114_notifications_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_config (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_by UUID NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_config")
