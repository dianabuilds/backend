"""Add moderation metadata for nodes.

Revision ID: 0103_nodes_moderation
Revises: 0102_feature_flags_sql_apply
Create Date: 2025-10-01
"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.exc import SAWarning

revision = "0103_nodes_moderation"
down_revision = "0102_feature_flags_sql_apply"
branch_labels = None
depends_on = None

_ALLOWED_STATUSES = ("pending", "resolved", "hidden", "restricted", "escalated")


def _ensure_pgcrypto_extension() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        # Extension creation may fail in restricted environments; ignore silently.
        pass


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _ensure_pgcrypto_extension()

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "Did not recognize type 'vector'", SAWarning)
        node_columns = {col["name"] for col in inspector.get_columns("nodes")}

    if "moderation_status" not in node_columns:
        op.add_column("nodes", sa.Column("moderation_status", sa.Text(), nullable=True))
        op.execute(
            sa.text(
                "UPDATE nodes SET moderation_status = CASE "
                "WHEN status = 'published' THEN 'resolved' "
                "WHEN status IN ('deleted','archived') THEN 'hidden' "
                "ELSE 'pending' END"
            )
        )
    op.execute(
        sa.text("UPDATE nodes SET moderation_status = COALESCE(moderation_status, 'pending')")
    )
    op.execute(sa.text("ALTER TABLE nodes ALTER COLUMN moderation_status SET DEFAULT 'pending'"))
    op.alter_column(
        "nodes",
        "moderation_status",
        existing_type=sa.Text(),
        nullable=False,
        server_default=sa.text("'pending'"),
    )

    if "moderation_status_updated_at" not in node_columns:
        op.add_column(
            "nodes",
            sa.Column(
                "moderation_status_updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.execute(
            sa.text(
                "UPDATE nodes "
                "SET moderation_status_updated_at = COALESCE(moderation_status_updated_at, updated_at, created_at, now())"
            )
        )

    op.execute("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_moderation_status_chk")
    op.create_check_constraint(
        "nodes_moderation_status_chk",
        "nodes",
        "moderation_status IN ('pending','resolved','hidden','restricted','escalated')",
    )

    op.execute("DROP INDEX IF EXISTS ix_nodes_moderation_status")
    op.create_index(
        "ix_nodes_moderation_status",
        "nodes",
        ["moderation_status", "updated_at"],
    )

    if not inspector.has_table("node_moderation_history"):
        op.create_table(
            "node_moderation_history",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("node_id", sa.BigInteger(), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("actor_id", sa.Text(), nullable=True),
            sa.Column(
                "decided_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "payload",
                pg.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_node_moderation_history_node",
            "node_moderation_history",
            ["node_id", "decided_at"],
        )
    else:
        try:
            existing_indexes = {
                idx["name"] for idx in inspector.get_indexes("node_moderation_history")
            }
        except sa.exc.NoSuchTableError:
            existing_indexes = set()
        if "ix_node_moderation_history_node" not in existing_indexes:
            op.create_index(
                "ix_node_moderation_history_node",
                "node_moderation_history",
                ["node_id", "decided_at"],
            )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_node_moderation_history_node")
    op.drop_table("node_moderation_history")
    op.execute("DROP INDEX IF EXISTS ix_nodes_moderation_status")
    op.execute("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_moderation_status_chk")
    op.drop_column("nodes", "moderation_status_updated_at")
    op.drop_column("nodes", "moderation_status")
