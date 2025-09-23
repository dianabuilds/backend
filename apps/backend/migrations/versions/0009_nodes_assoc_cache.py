"""
Create node_assoc_cache for related nodes caching

Revision ID: 0009
Revises: 0008
Create Date: 2025-09-19
"""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS node_assoc_cache (
          source_id bigint NOT NULL,
          target_id bigint NOT NULL,
          algo text NOT NULL,
          score double precision NOT NULL DEFAULT 0,
          updated_at timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (source_id, target_id, algo)
        );
        CREATE INDEX IF NOT EXISTS ix_node_assoc_cache_source_algo ON node_assoc_cache(source_id, algo, updated_at DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_node_assoc_cache_source_algo;")
    op.execute("DROP TABLE IF EXISTS node_assoc_cache;")
