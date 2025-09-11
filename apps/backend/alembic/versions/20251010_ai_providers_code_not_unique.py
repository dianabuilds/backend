"""Make ai_providers.code not unique

Revision ID: 20251010_ai_providers_code_not_unique
Revises: 20251010_ai_system_v2
Create Date: 2025-10-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251010_ai_providers_code_not_unique"
down_revision = "20251010_ai_system_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop unique constraint on ai_providers.code if it exists
    try:
        op.drop_constraint("ai_providers_code_key", "ai_providers", type_="unique")
    except Exception:
        # Some databases name constraints differently; try generic approach
        pass
    # Create non-unique index for faster lookups by code
    try:
        op.create_index("ix_ai_providers_code", "ai_providers", ["code"], unique=False)
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    try:
        op.drop_index("ix_ai_providers_code", table_name="ai_providers")
    except Exception:
        pass
    op.create_unique_constraint(
        "ai_providers_code_key", "ai_providers", ["code"]
    )  # may fail if duplicates exist
