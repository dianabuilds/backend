"""Drop slug unique constraint for home configs.

Revision ID: 0109_home_config_drop_slug_unique
Revises: 0109_home_config_audit_comments
Create Date: 2025-10-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0109_home_config_drop_slug_unique"
down_revision = "0109_home_config_audit_comments"
branch_labels = None
depends_on = None


_TABLE_NAME = "product_home_configs"
_CONSTRAINT_NAME = "ux_product_home_configs_slug"


def _has_unique(inspector: sa.Inspector, table: str, name: str) -> bool:
    try:
        uniques = inspector.get_unique_constraints(table)
    except Exception:
        return False
    return any(constraint.get("name") == name for constraint in uniques)


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")
    inspector = sa.inspect(bind)
    if not inspector.has_table(_TABLE_NAME):
        return
    if _has_unique(inspector, _TABLE_NAME, _CONSTRAINT_NAME):
        op.drop_constraint(_CONSTRAINT_NAME, _TABLE_NAME, type_="unique")


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")
    inspector = sa.inspect(bind)
    if not inspector.has_table(_TABLE_NAME):
        return
    if not _has_unique(inspector, _TABLE_NAME, _CONSTRAINT_NAME):
        op.create_unique_constraint(_CONSTRAINT_NAME, _TABLE_NAME, ["slug"])
