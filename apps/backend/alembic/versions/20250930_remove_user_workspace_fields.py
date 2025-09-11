"""Drop users.default_workspace_id / default_tenant_id

Revision ID: 20250930_remove_user_workspace_fields
Revises: 20250910_fix_missing_user_default_workspace, 20250921_workspace_to_tenant
Create Date: 2025-09-30

This migration finalizes the removal of legacy workspace/tenant default
column from the users table. It drops both possible names depending on
what earlier branch created or renamed it.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250930_remove_user_workspace_fields"
down_revision = "20250921_workspace_to_tenant"
branch_labels = None
depends_on = None


def _has_column(conn: sa.Connection, table: str, column: str) -> bool:
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "users", "default_tenant_id"):
        op.drop_column("users", "default_tenant_id")
    if _has_column(bind, "users", "default_workspace_id"):
        op.drop_column("users", "default_workspace_id")


def downgrade() -> None:  # pragma: no cover
    # No automatic downgrade; re-adding the column is harmless but not needed.
    pass
