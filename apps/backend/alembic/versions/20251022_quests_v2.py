"""Create quests_v2 table (decoupled from nodes)

Revision ID: 20251022_quests_v2
Revises: 20251022_tag_usage_counters
Create Date: 2025-10-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20251022_quests_v2"
down_revision = "20251022_tag_usage_counters"
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
    if "quests_v2" in insp.get_table_names():
        return
    author_type = _pg_uuid()
    op.create_table(
        "quests_v2",
        sa.Column("id", author_type, primary_key=True, nullable=False),
        sa.Column("author_id", author_type, nullable=False, index=True),
        sa.Column("slug", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("tags", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    try:
        op.create_index("ix_quests_v2_author_id", "quests_v2", ["author_id"], unique=False)
    except Exception:
        pass
    try:
        op.create_unique_constraint("uq_quests_v2_slug", "quests_v2", ["slug"])
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    try:
        op.drop_constraint("uq_quests_v2_slug", table_name="quests_v2", type_="unique")
    except Exception:
        pass
    try:
        op.drop_index("ix_quests_v2_author_id", table_name="quests_v2")
    except Exception:
        pass
    try:
        op.drop_table("quests_v2")
    except Exception:
        pass
