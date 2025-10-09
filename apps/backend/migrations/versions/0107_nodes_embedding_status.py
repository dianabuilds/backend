"""Add embedding readiness/status columns to nodes.

Revision ID: 0107_nodes_embedding_status
Revises: 0106_node_engagement
Create Date: 2025-10-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Register pgvector type for reflection if available
try:  # pragma: no cover
    from sqlalchemy.dialects.postgresql import base as pg_base

    class _VectorPlaceholder(sa.types.NullType):  # pragma: no cover
        def __init__(self, *args, **kwargs):
            super().__init__()

    pg_base.ischema_names["vector"] = _VectorPlaceholder
except Exception:  # pragma: no cover
    pass

revision = "0107_nodes_embedding_status"
down_revision = "0106_node_engagement"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "nodes", "embedding_ready"):
        op.add_column(
            "nodes",
            sa.Column(
                "embedding_ready",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if not _has_column(inspector, "nodes", "embedding_status"):
        op.add_column(
            "nodes",
            sa.Column(
                "embedding_status",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'pending'"),
            ),
        )

    op.execute(
        sa.text(
            "UPDATE nodes SET embedding_ready = TRUE, embedding_status = 'ready' WHERE embedding IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE nodes SET embedding_ready = FALSE, embedding_status = 'pending' WHERE embedding IS NULL"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("nodes")}

    if "embedding_status" in columns:
        op.drop_column("nodes", "embedding_status")
    if "embedding_ready" in columns:
        op.drop_column("nodes", "embedding_ready")
