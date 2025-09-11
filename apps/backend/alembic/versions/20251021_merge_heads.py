"""Merge heads: ai_providers_code_not_unique + remove_account_fields

Revision ID: 20251021_merge_heads
Revises: 20251010_ai_providers_code_not_unique, 20251020_remove_account_fields
Create Date: 2025-10-21

This is a no-op merge that unifies two concurrent heads:
- 20251010_ai_providers_code_not_unique
- 20251020_remove_account_fields

It establishes a single linear history for subsequent revisions.
"""

from __future__ import annotations

from alembic import op  # noqa: F401  (import kept for consistency)

# revision identifiers, used by Alembic.
revision = "20251021_merge_heads"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge
    pass


def downgrade() -> None:  # pragma: no cover
    # Not supported; splitting history is not practical.
    pass

