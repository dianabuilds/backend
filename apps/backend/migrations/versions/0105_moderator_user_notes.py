"""Add moderator user notes table.

Revision ID: 0105_moderator_user_notes
Revises: 0104_platform_moderation_state
Create Date: 2025-10-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0105_moderator_user_notes"
down_revision = "0104_platform_moderation_state"
branch_labels = None
depends_on = None


def _ensure_pgcrypto_extension() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        # Extension creation may fail on managed Postgres or read-only users.
        pass


def _ensure_indexes(bind: sa.engine.Connection) -> None:
    inspector = sa.inspect(bind)
    existing_indexes = {
        idx["name"] for idx in inspector.get_indexes("moderator_user_notes")
    }
    if "ix_moderator_user_notes_user" not in existing_indexes:
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_moderator_user_notes_user"
                " ON moderator_user_notes (user_id, pinned, created_at)"
            )
        )
    if "ix_moderator_user_notes_created_at" not in existing_indexes:
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_moderator_user_notes_created_at"
                " ON moderator_user_notes (created_at)"
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_pgcrypto_extension()

    inspector = sa.inspect(bind)
    if not inspector.has_table("moderator_user_notes"):
        op.create_table(
            "moderator_user_notes",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("author_id", sa.Text(), nullable=True),
            sa.Column("author_name", sa.Text(), nullable=True),
            sa.Column(
                "meta",
                pg.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "pinned",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
    _ensure_indexes(bind)


def downgrade() -> None:
    bind = op.get_bind()
    op.execute(sa.text("DROP INDEX IF EXISTS ix_moderator_user_notes_created_at"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_moderator_user_notes_user"))
    inspector = sa.inspect(bind)
    if inspector.has_table("moderator_user_notes"):
        op.drop_table("moderator_user_notes")
