"""add roles (enum) and user_roles table

Revision ID: c2d3e4f5a6b7
Revises: b5d6c7e8f901
Create Date: 2025-09-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b5d6c7e8f901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure enum type exists (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'user_role' AND n.nspname = current_schema()
            ) THEN
                CREATE TYPE user_role AS ENUM ('user','editor','moderator','admin');
            END IF;
        END$$;
        """
    )

    # M2M user_roles with composite PK
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role",
            pg.ENUM("user", "editor", "moderator", "admin", name="user_role", create_type=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "granted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_user_roles_user", "user_roles", ["user_id"])

    # Grant default role 'user' to all existing users
    op.execute(
        """
        INSERT INTO user_roles (user_id, role)
        SELECT id, 'user'::user_role FROM users
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_user_roles_user", table_name="user_roles")
    op.drop_table("user_roles")
    # Drop enum last (if not used elsewhere)
    try:
        pg.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
