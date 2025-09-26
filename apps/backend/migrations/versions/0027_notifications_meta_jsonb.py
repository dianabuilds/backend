"""convert notifications meta to jsonb

Revision ID: 0027
Revises: 0026
Create Date: 2025-09-25 23:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "notifications",
        "meta",
        type_=pg.JSONB(astext_type=sa.Text()),
        existing_type=sa.Text(),
        postgresql_using="meta::jsonb",
        server_default=sa.text("'{}'::jsonb"),
    )


def downgrade() -> None:
    op.alter_column(
        "notifications",
        "meta",
        type_=sa.Text(),
        existing_type=pg.JSONB(astext_type=sa.Text()),
        postgresql_using="meta::text",
        server_default=None,
    )
