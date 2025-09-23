"""
Baseline empty revision for DDD backend

Revision ID: 0001
Revises: None
Create Date: 2025-09-14

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = "20251010_ai_providers_code_not_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Initial baseline: no-op
    pass


def downgrade() -> None:
    # Initial baseline: no-op
    pass
