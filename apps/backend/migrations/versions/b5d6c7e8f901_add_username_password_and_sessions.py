"""add username/password and user_sessions

Revision ID: b5d6c7e8f901
Revises: 0004
Create Date: 2025-09-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "b5d6c7e8f901"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Add username and password_hash to users
    op.add_column("users", sa.Column("username", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))

    # Backfill username for existing rows if any, ensure uniqueness via random suffix
    op.execute(
        """
        UPDATE users
        SET username = COALESCE(
            NULLIF(username, ''),
            'user_' || substr(replace(gen_random_uuid()::text, '-', ''), 1, 12)
        )
        """
    )

    # Case-insensitive unique index on username
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'uq_users_username_lower' AND n.nspname = current_schema()
            ) THEN
                CREATE UNIQUE INDEX uq_users_username_lower ON users ((lower(username)));
            END IF;
        END$$;
        """
    )

    # Make username NOT NULL
    op.alter_column("users", "username", nullable=False)

    # Sessions table (cookie-based sessions and refresh tokens)
    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("refresh_token_hash", sa.Text(), nullable=True, unique=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_user_sessions_user", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_expires", "user_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_user_sessions_expires", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user", table_name="user_sessions")
    op.drop_table("user_sessions")

    # Drop username unique index and columns
    op.execute("DROP INDEX IF EXISTS uq_users_username_lower")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
