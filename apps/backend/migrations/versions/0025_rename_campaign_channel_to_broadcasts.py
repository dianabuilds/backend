"""rename notification campaigns channel to broadcasts

Revision ID: 0025
Revises: 0024
Create Date: 2025-09-26
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    ).scalar()
    return result is not None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        text(
            """
            INSERT INTO notification_channels (
                key,
                display_name,
                description,
                category,
                feature_flag_slug,
                flag_fallback_enabled,
                supports_digest,
                requires_consent,
                is_active,
                position,
                meta,
                created_at,
                updated_at
            )
            SELECT
                'broadcasts',
                'Broadcasts',
                description,
                category,
                'notifications.channel.broadcasts',
                flag_fallback_enabled,
                supports_digest,
                requires_consent,
                is_active,
                position,
                meta,
                created_at,
                updated_at
            FROM notification_channels
            WHERE key = 'campaigns'
            ON CONFLICT (key) DO NOTHING
            """
        )
    )

    migrations = [
        ("notification_topic_rules", "channel_key"),
        ("notification_preferences", "channel"),
        ("notification_preferences", "channel_key"),
        ("notification_consent_audit", "channel_key"),
        ("notifications", "channel_key"),
    ]
    for table, column in migrations:
        if _column_exists(conn, table, column):
            conn.execute(
                text(f"UPDATE {table} SET {column} = 'broadcasts' WHERE {column} = 'campaigns'")
            )

    conn.execute(
        text(
            """
            UPDATE feature_flags
            SET key = 'notifications.channel.broadcasts'
            WHERE key = 'notifications.channel.campaigns'
            """
        )
    )

    conn.execute(text("DELETE FROM notification_channels WHERE key = 'campaigns'"))


def downgrade() -> None:
    raise RuntimeError("Downgrading the broadcasts channel rename is not supported")
