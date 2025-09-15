"""Add tag_usage_counters projection table

Revision ID: 20251022_tag_usage_counters
Revises: 20250911_add_tenant_id_columns
Create Date: 2025-10-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251022_tag_usage_counters"
down_revision = "20250911_add_tenant_id_columns"
branch_labels = None
depends_on = None


def _pg_uuid():
    try:
        return sa.dialects.postgresql.UUID(as_uuid=True)  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        return sa.String(length=36)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tag_usage_counters" in insp.get_table_names():
        return
    author_type = _pg_uuid()
    op.create_table(
        "tag_usage_counters",
        sa.Column("author_id", author_type, primary_key=True, nullable=False),
        sa.Column("slug", sa.String, primary_key=True, nullable=False),
        sa.Column("count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    try:
        op.create_index("ix_tag_usage_counters_author", "tag_usage_counters", ["author_id"], unique=False)
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    try:
        op.drop_index("ix_tag_usage_counters_author", table_name="tag_usage_counters")
    except Exception:
        pass
    try:
        op.drop_table("tag_usage_counters")
    except Exception:
        pass
