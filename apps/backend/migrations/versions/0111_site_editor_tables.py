"""Site editor tables for pages and global blocks.

Revision ID: 0111_site_editor_tables
Revises: 0110_nodes_notifications_indexes
Create Date: 2025-10-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0111_site_editor_tables"
down_revision = "0110_nodes_notifications_indexes"
branch_labels = None
depends_on = None

PAGE_TYPE_ENUM = "site_page_type"
PAGE_STATUS_ENUM = "site_page_status"
REVIEW_STATUS_ENUM = "site_page_review_status"
BLOCK_STATUS_ENUM = "site_global_block_status"


def _create_enum(bind, name: str, values: list[str]) -> pg.ENUM:
    enum = pg.ENUM(*values, name=name, create_type=False)
    enum.create(bind, checkfirst=True)
    return enum


def _drop_enum(bind, name: str) -> None:
    enum = pg.ENUM(name=name, create_type=False)
    enum.drop(bind, checkfirst=True)


def _ensure_pgcrypto() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        pass


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)
    _ensure_pgcrypto()

    page_type_enum = _create_enum(
        bind,
        PAGE_TYPE_ENUM,
        ["landing", "collection", "article", "system"],
    )
    page_status_enum = _create_enum(
        bind,
        PAGE_STATUS_ENUM,
        ["draft", "published", "archived"],
    )
    review_status_enum = _create_enum(
        bind,
        REVIEW_STATUS_ENUM,
        ["none", "pending", "approved", "rejected"],
    )
    block_status_enum = _create_enum(
        bind,
        BLOCK_STATUS_ENUM,
        ["draft", "published", "archived"],
    )

    json_type = pg.JSONB(astext_type=sa.Text())

    if not inspector.has_table("site_pages"):
        op.create_table(
            "site_pages",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("slug", sa.Text(), nullable=False, unique=True),
            sa.Column("type", page_type_enum, nullable=False),
            sa.Column(
                "status",
                page_status_enum,
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("locale", sa.Text(), nullable=False, server_default=sa.text("'ru'")),
            sa.Column("owner", sa.Text(), nullable=True),
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
            sa.Column("published_version", sa.BigInteger(), nullable=True),
            sa.Column("draft_version", sa.BigInteger(), nullable=True),
            sa.Column(
                "has_pending_review", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
        )
        op.create_index("ix_site_pages_slug", "site_pages", ["slug"])
        op.create_index("ix_site_pages_status", "site_pages", ["status"])
        op.create_index("ix_site_pages_type", "site_pages", ["type"])

    if not inspector.has_table("site_page_drafts"):
        op.create_table(
            "site_page_drafts",
            sa.Column(
                "page_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
            sa.Column("data", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("meta", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column(
                "review_status",
                review_status_enum,
                nullable=False,
                server_default=sa.text("'none'"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("updated_by", sa.Text(), nullable=True),
        )

    if not inspector.has_table("site_page_versions"):
        op.create_table(
            "site_page_versions",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "page_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version", sa.BigInteger(), nullable=False),
            sa.Column("data", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("meta", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("diff", json_type, nullable=True),
            sa.Column(
                "published_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("published_by", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_site_page_versions_page_version",
            "site_page_versions",
            ["page_id", "version"],
            unique=True,
        )

    if not inspector.has_table("site_global_blocks"):
        op.create_table(
            "site_global_blocks",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("key", sa.Text(), nullable=False, unique=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("section", sa.Text(), nullable=False, server_default=sa.text("'general'")),
            sa.Column("locale", sa.Text(), nullable=True),
            sa.Column(
                "status",
                block_status_enum,
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column(
                "review_status",
                review_status_enum,
                nullable=False,
                server_default=sa.text("'none'"),
            ),
            sa.Column("data", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("meta", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column("published_version", sa.BigInteger(), nullable=True),
            sa.Column("draft_version", sa.BigInteger(), nullable=True),
            sa.Column(
                "requires_publisher", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("usage_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        )
        op.create_index(
            "ix_site_global_blocks_section_status",
            "site_global_blocks",
            ["section", "status"],
        )

    if not inspector.has_table("site_global_block_versions"):
        op.create_table(
            "site_global_block_versions",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "block_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_global_blocks.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version", sa.BigInteger(), nullable=False),
            sa.Column("data", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("meta", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("diff", json_type, nullable=True),
            sa.Column(
                "published_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("published_by", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_site_global_block_versions_block_version",
            "site_global_block_versions",
            ["block_id", "version"],
            unique=True,
        )

    if not inspector.has_table("site_global_block_usage"):
        op.create_table(
            "site_global_block_usage",
            sa.Column(
                "block_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_global_blocks.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "page_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("section", sa.Text(), primary_key=True, nullable=False),
        )

    if not inspector.has_table("site_page_metrics"):
        op.create_table(
            "site_page_metrics",
            sa.Column(
                "page_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("period", sa.Text(), primary_key=True, nullable=False),
            sa.Column(
                "locale",
                sa.Text(),
                primary_key=True,
                nullable=False,
                server_default=sa.text("'ru'"),
            ),
            sa.Column("range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False),
            sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("views", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("unique_users", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("cta_clicks", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("conversions", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("avg_time_on_page", sa.Numeric(12, 4), nullable=True),
            sa.Column("bounce_rate", sa.Numeric(7, 4), nullable=True),
            sa.Column("mobile_share", sa.Numeric(7, 4), nullable=True),
            sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'ok'")),
            sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
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
        )
        op.create_index(
            "ix_site_page_metrics_range_desc",
            "site_page_metrics",
            ["page_id", "period", "locale", "range_end"],
        )

    if not inspector.has_table("site_global_block_metrics"):
        op.create_table(
            "site_global_block_metrics",
            sa.Column(
                "block_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("site_global_blocks.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("period", sa.Text(), primary_key=True, nullable=False),
            sa.Column(
                "locale",
                sa.Text(),
                primary_key=True,
                nullable=False,
                server_default=sa.text("'ru'"),
            ),
            sa.Column("range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False),
            sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("impressions", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("clicks", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("conversions", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("revenue", sa.Numeric(14, 4), nullable=True),
            sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'ok'")),
            sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
            sa.Column("top_pages", json_type, nullable=True),
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
        )
        op.create_index(
            "ix_site_global_block_metrics_range_desc",
            "site_global_block_metrics",
            ["block_id", "period", "locale", "range_end"],
        )

    if not inspector.has_table("site_audit_log"):
        op.create_table(
            "site_audit_log",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("entity_type", sa.Text(), nullable=False),
            sa.Column("entity_id", pg.UUID(as_uuid=True), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("snapshot", json_type, nullable=True),
            sa.Column("actor", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index(
            "ix_site_audit_entity",
            "site_audit_log",
            ["entity_type", "entity_id"],
        )
        op.create_index(
            "ix_site_audit_created_at",
            "site_audit_log",
            ["created_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)

    if inspector.has_table("site_audit_log"):
        op.drop_index("ix_site_audit_created_at", table_name="site_audit_log")
        op.drop_index("ix_site_audit_entity", table_name="site_audit_log")
        op.drop_table("site_audit_log")

    if inspector.has_table("site_global_block_metrics"):
        op.drop_index(
            "ix_site_global_block_metrics_range_desc",
            table_name="site_global_block_metrics",
        )
        op.drop_table("site_global_block_metrics")

    if inspector.has_table("site_page_metrics"):
        op.drop_index(
            "ix_site_page_metrics_range_desc",
            table_name="site_page_metrics",
        )
        op.drop_table("site_page_metrics")

    if inspector.has_table("site_global_block_usage"):
        op.drop_table("site_global_block_usage")

    if inspector.has_table("site_global_block_versions"):
        op.drop_index(
            "ix_site_global_block_versions_block_version",
            table_name="site_global_block_versions",
        )
        op.drop_table("site_global_block_versions")

    if inspector.has_table("site_global_blocks"):
        op.drop_index(
            "ix_site_global_blocks_section_status",
            table_name="site_global_blocks",
        )
        op.drop_table("site_global_blocks")

    if inspector.has_table("site_page_versions"):
        op.drop_index(
            "ix_site_page_versions_page_version",
            table_name="site_page_versions",
        )
        op.drop_table("site_page_versions")

    if inspector.has_table("site_page_drafts"):
        op.drop_table("site_page_drafts")

    if inspector.has_table("site_pages"):
        op.drop_index("ix_site_pages_type", table_name="site_pages")
        op.drop_index("ix_site_pages_status", table_name="site_pages")
        op.drop_index("ix_site_pages_slug", table_name="site_pages")
        op.drop_table("site_pages")

    _drop_enum(bind, BLOCK_STATUS_ENUM)
    _drop_enum(bind, REVIEW_STATUS_ENUM)
    _drop_enum(bind, PAGE_STATUS_ENUM)
    _drop_enum(bind, PAGE_TYPE_ENUM)
