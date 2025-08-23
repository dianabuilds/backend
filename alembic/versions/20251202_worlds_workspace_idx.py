"""add indexes for worlds and characters workspace

Revision ID: 20251202_worlds_workspace_idx
Revises: 20251201_tags_workspace_idx
Create Date: 2025-12-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20251202_worlds_workspace_idx"
down_revision = "20251201_tags_workspace_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in ["world_templates", "characters"]:
        if table in inspector.get_table_names():
            indexes = {idx["name"] for idx in inspector.get_indexes(table)}
            idx_name = f"ix_{table}_workspace_id"
            if idx_name not in indexes:
                op.create_index(idx_name, table, ["workspace_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in ["world_templates", "characters"]:
        if table in inspector.get_table_names():
            idx_name = f"ix_{table}_workspace_id"
            indexes = {idx["name"] for idx in inspector.get_indexes(table)}
            if idx_name in indexes:
                op.drop_index(idx_name, table_name=table)
