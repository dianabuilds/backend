"""Add template flags and origin reference to site blocks.

Revision ID: 0132_site_block_template_flags
Revises: 0131_backfill_template_catalog_fields
Create Date: 2025-12-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0132_site_block_template_flags"
down_revision = "0131_backfill_template_catalog_fields"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column(
        "site_blocks",
        sa.Column(
            "is_template",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "site_blocks",
        sa.Column(
            "origin_block_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_blocks.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "site_blocks",
        sa.Column(
            "version",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_index(
        "ix_site_blocks_origin_block",
        "site_blocks",
        ["origin_block_id"],
    )

    # initialise version numbers from published/draft versions if present
    op.execute(
        sa.text(
            """
            UPDATE site_blocks
            SET version = COALESCE(published_version, draft_version, 0)
            """
        )
    )

    op.alter_column("site_blocks", "is_template", server_default=None)
    op.alter_column("site_blocks", "version", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_site_blocks_origin_block", table_name="site_blocks")
    op.drop_column("site_blocks", "version")
    op.drop_column("site_blocks", "origin_block_id")
    op.drop_column("site_blocks", "is_template")
