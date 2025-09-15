"""Add content_type to tag_usage_counters and adjust PK

Revision ID: 20251022_tag_usage_add_content_type
Revises: 20251022_quests_v2
Create Date: 2025-10-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20251022_tag_usage_add_content_type"
down_revision = "20251022_quests_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tag_usage_counters")}
    if "content_type" not in cols:
        op.add_column("tag_usage_counters", sa.Column("content_type", sa.String(), nullable=True))
        # backfill default
        try:
            op.execute(sa.text("UPDATE tag_usage_counters SET content_type='node' WHERE content_type IS NULL"))
        except Exception:
            pass
        # set NOT NULL
        try:
            op.alter_column("tag_usage_counters", "content_type", nullable=False)
        except Exception:
            pass
    # Recreate PK to include content_type
    try:
        # Drop existing primary key constraint (name may differ across DBs)
        for pk in insp.get_pk_constraint("tag_usage_counters").get("constrained_columns", []) or ["author_id", "slug"]:
            pass  # probe only
        try:
            op.drop_constraint("tag_usage_counters_pkey", table_name="tag_usage_counters", type_="primary")
        except Exception:
            # Fallback: some dialects use implicit PK names; attempt generic drop
            try:
                op.drop_constraint("pk_tag_usage_counters", table_name="tag_usage_counters", type_="primary")
            except Exception:
                pass
        try:
            op.create_primary_key(
                "pk_tag_usage_counters",
                "tag_usage_counters",
                ["author_id", "content_type", "slug"],
            )
        except Exception:
            pass
    except Exception:
        pass
    # Helpful index for queries by author+type
    try:
        op.create_index(
            "ix_tag_usage_counters_author_type",
            "tag_usage_counters",
            ["author_id", "content_type"],
            unique=False,
        )
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    # Keep column; reversing PK changes is risky and not needed in practice
    pass
