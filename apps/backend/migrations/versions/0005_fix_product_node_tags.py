"""
Ensure product_node_tags table exists and migrate data

Revision ID: 0005_fix_product_node_tags
Revises: 0004
Create Date: 2025-09-19
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_fix_product_node_tags"
down_revision = ("0004", "c2d3e4f5a6b7")
branch_labels = None
depends_on = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS product_node_tags (
  node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  slug text NOT NULL,
  PRIMARY KEY (node_id, slug)
);
"""

CREATE_INDEX_SQL = (
    """CREATE INDEX IF NOT EXISTS ix_product_node_tags_slug ON product_node_tags(slug);"""
)

COPY_DATA_SQL = """
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'node_tags') THEN
    INSERT INTO product_node_tags(node_id, slug)
    SELECT node_id, slug FROM node_tags
    ON CONFLICT DO NOTHING;
  END IF;
END$$;
"""

DROP_OLD_SQL = "DROP TABLE IF EXISTS node_tags CASCADE;"


def upgrade() -> None:
    op.execute(CREATE_TABLE_SQL)
    op.execute(CREATE_INDEX_SQL)
    op.execute(COPY_DATA_SQL)
    op.execute(DROP_OLD_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS product_node_tags CASCADE;")
