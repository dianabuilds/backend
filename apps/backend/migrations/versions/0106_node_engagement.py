"""Add node engagement tables and counters.

Revision ID: 0106_node_engagement
Revises: 0105_moderator_user_notes
Create Date: 2025-10-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0106_node_engagement"
down_revision = "0105_moderator_user_notes"
branch_labels = None
depends_on = None

# Register pgvector type for inspectors to avoid SAWarning during column introspection.
try:  # pragma: no cover - defensive guard for environments without pgvector
    from sqlalchemy.dialects.postgresql import base as pg_base

    if "vector" not in pg_base.ischema_names:
        pg_base.ischema_names["vector"] = sa.types.NullType
except Exception:  # pragma: no cover
    pass


_NEW_NODE_COLUMNS: tuple[tuple[str, sa.Column], ...] = (
    (
        "views_count",
        sa.Column(
            "views_count",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    ),
    (
        "reactions_like_count",
        sa.Column(
            "reactions_like_count",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    ),
    (
        "comments_disabled",
        sa.Column(
            "comments_disabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    ),
    (
        "comments_locked_by",
        sa.Column("comments_locked_by", pg.UUID(as_uuid=True), nullable=True),
    ),
    (
        "comments_locked_at",
        sa.Column(
            "comments_locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    ),
)

_NODE_INDEXES: tuple[tuple[str, str], ...] = (
    (
        "ix_nodes_views_count",
        "CREATE INDEX IF NOT EXISTS ix_nodes_views_count ON nodes (views_count DESC, id)",
    ),
    (
        "ix_nodes_reactions_like_count",
        "CREATE INDEX IF NOT EXISTS ix_nodes_reactions_like_count ON nodes (reactions_like_count DESC, id)",
    ),
    (
        "ix_nodes_comments_disabled",
        "CREATE INDEX IF NOT EXISTS ix_nodes_comments_disabled ON nodes (comments_disabled, id)",
    ),
)


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _ensure_node_columns() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for name, column in _NEW_NODE_COLUMNS:
        if not _has_column(inspector, "nodes", name):
            op.add_column("nodes", column.copy())

    # Ensure predictable server defaults for newly added columns (idempotent)
    for name, _column in _NEW_NODE_COLUMNS:
        if name in {"views_count", "reactions_like_count"}:
            op.alter_column("nodes", name, server_default=sa.text("0"))
        elif name == "comments_disabled":
            op.alter_column("nodes", name, server_default=sa.text("false"))
        elif name == "comments_locked_by":
            op.alter_column("nodes", name, server_default=None)
        elif name == "comments_locked_at":
            op.alter_column("nodes", name, server_default=None)

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("nodes")}
    for idx_name, sql in _NODE_INDEXES:
        if idx_name not in existing_indexes:
            op.execute(sa.text(sql))


def _create_node_views_daily() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("node_views_daily"):
        return
    op.create_table(
        "node_views_daily",
        sa.Column("node_id", sa.BigInteger(), nullable=False),
        sa.Column("bucket_date", sa.Date(), nullable=False),
        sa.Column(
            "views",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("node_id", "bucket_date"),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_node_views_daily_date",
        "node_views_daily",
        ["bucket_date", "node_id"],
    )


def _create_node_reactions() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("node_reactions"):
        return
    op.create_table(
        "node_reactions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("node_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reaction_type",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'like'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "node_id", "user_id", "reaction_type", name="ux_node_reactions_unique"
        ),
        sa.CheckConstraint(
            "char_length(reaction_type) >= 1 AND char_length(reaction_type) <= 32",
            name="node_reactions_reaction_type_chk",
        ),
    )
    op.create_index(
        "ix_node_reactions_node",
        "node_reactions",
        ["node_id", "reaction_type", "created_at"],
    )
    op.create_index(
        "ix_node_reactions_user",
        "node_reactions",
        ["user_id", "created_at"],
    )


def _create_node_comments() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("node_comments"):
        return
    op.create_table(
        "node_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("node_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_comment_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "depth",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'published'"),
        ),
        sa.Column(
            "metadata",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"], ["node_comments.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "status IN ('pending','published','hidden','deleted','blocked')",
            name="node_comments_status_chk",
        ),
        sa.CheckConstraint(
            "depth >= 0 AND depth <= 5",
            name="node_comments_depth_chk",
        ),
    )
    op.create_index(
        "ix_node_comments_node_created",
        "node_comments",
        ["node_id", "created_at"],
    )
    op.create_index(
        "ix_node_comments_parent",
        "node_comments",
        ["parent_comment_id", "created_at"],
    )
    op.create_index(
        "ix_node_comments_author",
        "node_comments",
        ["author_id", "created_at"],
    )

    if not inspector.has_table("node_comment_bans"):
        op.create_table(
            "node_comment_bans",
            sa.Column("node_id", sa.BigInteger(), nullable=False),
            sa.Column("target_user_id", pg.UUID(as_uuid=True), nullable=False),
            sa.Column("set_by", pg.UUID(as_uuid=True), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.PrimaryKeyConstraint("node_id", "target_user_id"),
            sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_node_comment_bans_set_by",
            "node_comment_bans",
            ["set_by", "created_at"],
        )


def upgrade() -> None:
    _ensure_node_columns()
    _create_node_views_daily()
    _create_node_reactions()
    _create_node_comments()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("node_comment_bans"):
        op.drop_index("ix_node_comment_bans_set_by", table_name="node_comment_bans")
        op.drop_table("node_comment_bans")

    if inspector.has_table("node_comments"):
        op.drop_index("ix_node_comments_author", table_name="node_comments")
        op.drop_index("ix_node_comments_parent", table_name="node_comments")
        op.drop_index("ix_node_comments_node_created", table_name="node_comments")
        op.drop_table("node_comments")

    if inspector.has_table("node_reactions"):
        op.drop_index("ix_node_reactions_user", table_name="node_reactions")
        op.drop_index("ix_node_reactions_node", table_name="node_reactions")
        op.drop_table("node_reactions")

    if inspector.has_table("node_views_daily"):
        op.drop_index("ix_node_views_daily_date", table_name="node_views_daily")
        op.drop_table("node_views_daily")

    op.execute(sa.text("DROP INDEX IF EXISTS ix_nodes_comments_disabled"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_nodes_reactions_like_count"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_nodes_views_count"))

    existing_columns = {col["name"] for col in inspector.get_columns("nodes")}
    if "comments_locked_at" in existing_columns:
        op.drop_column("nodes", "comments_locked_at")
    if "comments_locked_by" in existing_columns:
        op.drop_column("nodes", "comments_locked_by")
    if "comments_disabled" in existing_columns:
        op.drop_column("nodes", "comments_disabled")
    if "reactions_like_count" in existing_columns:
        op.drop_column("nodes", "reactions_like_count")
    if "views_count" in existing_columns:
        op.drop_column("nodes", "views_count")
