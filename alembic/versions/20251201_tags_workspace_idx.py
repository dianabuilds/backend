"""make tags.workspace_id not null and indexed

Revision ID: 20251201_tags_workspace_idx
Revises: 20251101_ws_role_visibility
Create Date: 2025-12-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20251201_tags_workspace_idx"
down_revision = "20251101_ws_role_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "tags" in inspector.get_table_names():
        cols = {c["name"]: c for c in inspector.get_columns("tags")}
        if "workspace_id" in cols:
            if cols["workspace_id"].get("nullable", True):
                op.alter_column(
                    "tags",
                    "workspace_id",
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False,
                )
            indexes = {idx["name"] for idx in inspector.get_indexes("tags")}
            if "ix_tags_workspace_id" not in indexes:
                op.create_index("ix_tags_workspace_id", "tags", ["workspace_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "tags" in inspector.get_table_names():
        cols = {c["name"]: c for c in inspector.get_columns("tags")}
        if "workspace_id" in cols:
            indexes = {idx["name"] for idx in inspector.get_indexes("tags")}
            if "ix_tags_workspace_id" in indexes:
                op.drop_index("ix_tags_workspace_id", table_name="tags")
            if not cols["workspace_id"].get("nullable", True):
                op.alter_column(
                    "tags",
                    "workspace_id",
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True,
                )
