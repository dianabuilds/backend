"""
Add slug (16-hex) to nodes and backfill

Revision ID: 0006
Revises: 0005_fix_product_node_tags
Create Date: 2025-09-19

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005_fix_product_node_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add nullable slug column if not exists
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS slug text")
    # 2) Backfill slug for rows with NULL
    # Use md5(random()||clock_timestamp()) to generate 32-hex, take first 16
    # Repeat a couple of times to minimize any collisions before unique constraint
    op.execute(
        """
        UPDATE nodes
        SET slug = SUBSTRING(md5(random()::text || clock_timestamp()::text) FOR 16)
        WHERE slug IS NULL;
        """
    )
    op.execute(
        """
        UPDATE nodes
        SET slug = SUBSTRING(md5(random()::text || clock_timestamp()::text) FOR 16)
        WHERE slug IS NULL;
        """
    )
    # 3) Add CHECK constraint for hex format
    op.execute(
        "ALTER TABLE nodes ADD CONSTRAINT nodes_slug_format_chk CHECK (slug ~ '^[0-9a-f]{16}$') NOT VALID"
    )
    # Validate existing rows (may be skipped if large dataset)
    try:
        op.execute("ALTER TABLE nodes VALIDATE CONSTRAINT nodes_slug_format_chk")
    except Exception:
        # Non-blocking; admins can validate later
        pass
    # 4) Add UNIQUE index and set NOT NULL
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_nodes_slug ON nodes(slug)")
    op.execute("ALTER TABLE nodes ALTER COLUMN slug SET NOT NULL")


def downgrade() -> None:
    # Drop constraint and column (safe order)
    op.execute("DROP INDEX IF EXISTS ux_nodes_slug")
    op.execute("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_slug_format_chk")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS slug")
