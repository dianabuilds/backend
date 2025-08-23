"""add index for achievements workspace_id

Revision ID: 20251204_achievements_workspace_idx
Revises: 20251203_alembic_version_len
Create Date: 2025-12-04
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251204_achievements_workspace_idx"
down_revision = "20251203_alembic_version_len"
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.create_index(
            "ix_achievements_workspace_id",
            "achievements",
            ["workspace_id"],
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_achievements_workspace_id", table_name="achievements")
    except Exception:
        pass
