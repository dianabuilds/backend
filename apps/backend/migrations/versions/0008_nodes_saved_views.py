"""
Create product_node_saved_views for saved list views per user

Revision ID: 0008
Revises: 0007
Create Date: 2025-09-19

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS product_node_saved_views (
          id bigserial PRIMARY KEY,
          user_id uuid NOT NULL,
          name text NOT NULL,
          config jsonb NOT NULL,
          is_default boolean NOT NULL DEFAULT false,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(user_id, name)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_product_node_saved_views_user ON product_node_saved_views(user_id)"
    )
    # At most one default per user
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_product_node_saved_views_default ON product_node_saved_views(user_id) WHERE is_default"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_product_node_saved_views_default")
    op.execute("DROP INDEX IF EXISTS ix_product_node_saved_views_user")
    op.execute("DROP TABLE IF EXISTS product_node_saved_views")
