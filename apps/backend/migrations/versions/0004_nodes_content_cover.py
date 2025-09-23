"""
Add content_html and cover_url to nodes

Revision ID: 0004
Revises: 0003
Create Date: 2025-09-18

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable fields for rich content and cover image url
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS content_html text NULL")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS cover_url text NULL")


def downgrade() -> None:
    # Safe drop if present
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS content_html")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS cover_url")
