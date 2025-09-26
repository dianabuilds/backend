"""settings foundations: profile limits, notification preferences, wallet columns, session extensions

Revision ID: 0018
Revises: 0017
Create Date: 2025-09-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | None = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users wallet columns -------------------------------------------------
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_address text;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_chain_id text;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_nonce text;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_signature text;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_verified_at timestamptz;")

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_users_wallet_lower
        ON users ((lower(wallet_address)))
        WHERE wallet_address IS NOT NULL;
        """
    )

    # --- profile_change_limits ------------------------------------------------
    op.create_table(
        "profile_change_limits",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("last_username_change_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_email_change_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # --- notification_preferences --------------------------------------------
    op.create_table(
        "notification_preferences",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic_key", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("opt_in", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("digest", sa.Text(), nullable=False, server_default=sa.text("'none'")),
        sa.Column(
            "quiet_hours",
            pg.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "topic_key", "channel", name="pk_notification_preferences"
        ),
    )
    op.create_index(
        "ix_notification_preferences_topic",
        "notification_preferences",
        ["topic_key", "channel"],
    )

    # --- profile_email_change_requests ---------------------------------------
    op.create_table(
        "profile_email_change_requests",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("token", sa.Text(), nullable=False, unique=True),
        sa.Column("new_email", sa.Text(), nullable=False),
        sa.Column(
            "requested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_profile_email_change_requests_token",
        "profile_email_change_requests",
        ["token"],
        unique=True,
    )

    # --- user_sessions extensions --------------------------------------------
    op.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS device_id uuid;")
    op.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS platform_fingerprint text;")
    op.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS terminated_by uuid;")
    op.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS terminated_reason text;")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_sessions_device
        ON user_sessions (user_id, device_id)
        WHERE device_id IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_sessions_device;")
    op.execute(
        """
        ALTER TABLE user_sessions
            DROP COLUMN IF EXISTS terminated_reason,
            DROP COLUMN IF EXISTS terminated_by,
            DROP COLUMN IF EXISTS platform_fingerprint,
            DROP COLUMN IF EXISTS device_id;
        """
    )

    op.drop_index(
        "ix_profile_email_change_requests_token",
        table_name="profile_email_change_requests",
    )
    op.drop_table("profile_email_change_requests")

    op.drop_index("ix_notification_preferences_topic", table_name="notification_preferences")
    op.drop_table("notification_preferences")

    op.drop_table("profile_change_limits")

    op.execute("DROP INDEX IF EXISTS uq_users_wallet_lower;")
    op.execute(
        """
        ALTER TABLE users
            DROP COLUMN IF EXISTS wallet_verified_at,
            DROP COLUMN IF EXISTS wallet_signature,
            DROP COLUMN IF EXISTS wallet_nonce,
            DROP COLUMN IF EXISTS wallet_chain_id,
            DROP COLUMN IF EXISTS wallet_address;
        """
    )
