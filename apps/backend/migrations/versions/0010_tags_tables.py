"""
Ensure tags tables exist: tag, tag_usage_counters

Revision ID: 0010
Revises: 0009
Create Date: 2025-09-19
"""

from __future__ import annotations

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tag (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          slug text UNIQUE NOT NULL,
          name text NOT NULL,
          is_hidden boolean NOT NULL DEFAULT false,
          created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_tag_name ON tag (name);
        CREATE TABLE IF NOT EXISTS tag_usage_counters (
          author_id uuid NOT NULL,
          content_type text NOT NULL,
          slug text NOT NULL,
          count int NOT NULL DEFAULT 0,
          PRIMARY KEY (author_id, content_type, slug)
        );
        CREATE INDEX IF NOT EXISTS ix_tag_usage_slug ON tag_usage_counters(slug);
        CREATE INDEX IF NOT EXISTS ix_tag_usage_ctype ON tag_usage_counters(content_type);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tag_usage_ctype;")
    op.execute("DROP INDEX IF EXISTS ix_tag_usage_slug;")
    op.execute("DROP TABLE IF EXISTS tag_usage_counters;")
    op.execute("DROP INDEX IF EXISTS ix_tag_name;")
    op.execute("DROP TABLE IF EXISTS tag;")
