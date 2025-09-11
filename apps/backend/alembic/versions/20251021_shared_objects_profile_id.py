"""Rename shared_objects.account_id -> profile_id and update UC

Revision ID: 20251021_shared_objects_profile_id
Revises: 20251021_merge_heads
Create Date: 2025-10-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20251021_shared_objects_profile_id"
down_revision = "20251021_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    # Drop old UC if exists
    try:
        ucs = insp.get_unique_constraints("shared_objects")
        for uc in ucs:
            if uc.get("name") == "uq_shared_object":
                op.drop_constraint("uq_shared_object", table_name="shared_objects", type_="unique")
                break
    except Exception:
        pass
    # Rename column account_id -> profile_id if present
    cols = [c["name"] for c in insp.get_columns("shared_objects")]
    if "account_id" in cols and "profile_id" not in cols:
        op.alter_column("shared_objects", "account_id", new_column_name="profile_id")
    # Recreate UC on (object_type, object_id, profile_id)
    try:
        op.create_unique_constraint(
            "uq_shared_object", "shared_objects", ["object_type", "object_id", "profile_id"]
        )
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    raise NotImplementedError

