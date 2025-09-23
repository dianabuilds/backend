"""
Bridge stub for legacy migration tree.

Revision ID: 20251010_ai_providers_code_not_unique
Revises: None (legacy root)
Create Date: 2025-09-15

This is a no-op migration that serves as an anchor for databases
that were previously stamped with a legacy revision ID.
The new migration chain continues from this revision via 0001.
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "20251010_ai_providers_code_not_unique"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: historical anchor only
    pass


def downgrade() -> None:
    # No-op: historical anchor only
    pass
