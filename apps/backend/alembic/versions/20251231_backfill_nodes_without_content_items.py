from __future__ import annotations

from alembic import op


revision = "20251231_backfill_nodes_without_content_items"
down_revision = "20251230_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO content_items (
            id,
            node_id,
            workspace_id,
            type,
            status,
            visibility,
            version,
            slug,
            title,
            created_by_user_id,
            updated_by_user_id,
            published_at,
            created_at,
            updated_at
        )
        SELECT
            n.alt_id,
            n.id,
            n.workspace_id,
            'quest',
            n.status,
            n.visibility,
            COALESCE(n.version, 1),
            n.slug,
            COALESCE(n.title, 'Untitled'),
            n.created_by_user_id,
            n.updated_by_user_id,
            CASE WHEN n.status = 'published' THEN n.updated_at ELSE NULL END,
            n.created_at,
            n.updated_at
        FROM nodes n
        LEFT JOIN content_items ci ON ci.node_id = n.id
        WHERE ci.id IS NULL
        """
    )


def downgrade() -> None:
    pass
