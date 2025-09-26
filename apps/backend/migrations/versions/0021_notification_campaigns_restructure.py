"""placeholder for removed notification campaign restructure

Revision ID: 0021
Revises: 0020
Create Date: 2025-09-25
"""

from __future__ import annotations

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy migration removed; retained to keep Alembic history consistent.
    op.execute("SELECT 1")


def downgrade() -> None:
    raise RuntimeError("Downgrading past 0021 is not supported")
