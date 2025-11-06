"""Baseline migration for Site Editor tables.

Revision ID: 0131_backfill_template_catalog_fields
Revises: 0115_notifications_retention_config
Create Date: 2025-12-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0131_backfill_template_catalog_fields"
down_revision = "0115_notifications_retention_config"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


PAGE_TYPE_ENUM = pg.ENUM(
    "landing",
    "collection",
    "article",
    "system",
    name="site_page_type",
    create_type=True,
)

PAGE_STATUS_ENUM = pg.ENUM(
    "draft",
    "published",
    "archived",
    name="site_page_status",
    create_type=True,
)

PAGE_REVIEW_STATUS_ENUM = pg.ENUM(
    "none",
    "pending",
    "approved",
    "rejected",
    name="site_page_review_status",
    create_type=True,
)

BLOCK_STATUS_ENUM = pg.ENUM(
    "draft",
    "published",
    "archived",
    name="site_global_block_status",
    create_type=True,
)

BLOCK_SCOPE_ENUM = pg.ENUM(
    "page",
    "shared",
    name="site_block_scope",
    create_type=True,
)

JSONB = pg.JSONB(astext_type=sa.Text())
TEXT_ARRAY = pg.ARRAY(sa.Text(), dimensions=1)


def upgrade() -> None:
    bind = op.get_bind()
    PAGE_TYPE_ENUM.create(bind, checkfirst=True)
    PAGE_STATUS_ENUM.create(bind, checkfirst=True)
    PAGE_REVIEW_STATUS_ENUM.create(bind, checkfirst=True)
    BLOCK_STATUS_ENUM.create(bind, checkfirst=True)
    BLOCK_SCOPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "site_pages",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("type", PAGE_TYPE_ENUM, nullable=False),
        sa.Column(
            "status",
            PAGE_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "default_locale", sa.Text(), nullable=False, server_default=sa.text("'ru'")
        ),
        sa.Column(
            "available_locales",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "slug_localized",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("published_version", sa.BigInteger(), nullable=True),
        sa.Column("draft_version", sa.BigInteger(), nullable=True),
        sa.Column(
            "has_pending_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.create_index("ix_site_pages_slug", "site_pages", ["slug"], unique=False)
    op.create_index("ix_site_pages_status", "site_pages", ["status"], unique=False)
    op.create_index("ix_site_pages_type", "site_pages", ["type"], unique=False)

    op.create_table(
        "site_block_templates",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "section", sa.Text(), nullable=False, server_default=sa.text("'general'")
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'available'")
        ),
        sa.Column(
            "default_locale", sa.Text(), nullable=False, server_default=sa.text("'ru'")
        ),
        sa.Column(
            "available_locales",
            JSONB,
            nullable=False,
            server_default=sa.text("'[\"ru\"]'::jsonb"),
        ),
        sa.Column(
            "default_data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "default_meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("block_type", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("sources", TEXT_ARRAY, nullable=True),
        sa.Column("surfaces", TEXT_ARRAY, nullable=True),
        sa.Column("owners", TEXT_ARRAY, nullable=True),
        sa.Column("catalog_locales", TEXT_ARRAY, nullable=True),
        sa.Column("documentation_url", sa.Text(), nullable=True),
        sa.Column("keywords", TEXT_ARRAY, nullable=True),
        sa.Column("preview_kind", sa.Text(), nullable=True),
        sa.Column("status_note", sa.Text(), nullable=True),
        sa.Column(
            "requires_publisher",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "allow_shared_scope",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "allow_page_scope",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("shared_note", sa.Text(), nullable=True),
        sa.Column("key_prefix", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("updated_by", sa.Text(), nullable=True),
    )

    op.create_table(
        "site_page_drafts",
        sa.Column(
            "page_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "review_status",
            PAGE_REVIEW_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'none'"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("updated_by", sa.Text(), nullable=True),
    )

    op.create_table(
        "site_page_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "page_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("diff", JSONB, nullable=True),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("published_by", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_site_page_versions_page_version",
        "site_page_versions",
        ["page_id", "version"],
        unique=True,
    )

    op.create_table(
        "site_blocks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.Text(), nullable=True, unique=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "template_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_block_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "scope", BLOCK_SCOPE_ENUM, nullable=False, server_default=sa.text("'page'")
        ),
        sa.Column(
            "section", sa.Text(), nullable=False, server_default=sa.text("'general'")
        ),
        sa.Column(
            "default_locale", sa.Text(), nullable=False, server_default=sa.text("'ru'")
        ),
        sa.Column(
            "available_locales",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "status",
            BLOCK_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column(
            "review_status",
            PAGE_REVIEW_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'none'"),
        ),
        sa.Column("data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("published_version", sa.BigInteger(), nullable=True),
        sa.Column("draft_version", sa.BigInteger(), nullable=True),
        sa.Column(
            "requires_publisher",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("updated_by", sa.Text(), nullable=True),
    )
    op.create_index("ix_site_blocks_scope_status", "site_blocks", ["scope", "status"])
    op.create_index("ix_site_blocks_scope_section", "site_blocks", ["scope", "section"])
    op.create_index(
        "ix_site_blocks_template_scope", "site_blocks", ["template_id", "scope"]
    )

    op.create_table(
        "site_block_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "block_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("diff", JSONB, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_site_block_versions_block_version",
        "site_block_versions",
        ["block_id", "version"],
        unique=True,
    )

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
        sa.Column(
            "range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False
        ),
        sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "impressions", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "clicks", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "conversions", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("avg_time_on_page", sa.Numeric(12, 4), nullable=True),
        sa.Column("bounce_rate", sa.Numeric(7, 4), nullable=True),
        sa.Column("mobile_share", sa.Numeric(7, 4), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'ok'")),
        sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_site_page_metrics_range_desc",
        "site_page_metrics",
        ["page_id", "period", "locale", "range_end"],
    )

    op.create_table(
        "site_block_bindings",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "block_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "page_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_pages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column(
            "position", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "has_draft", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("last_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_site_block_bindings_block_page",
        "site_block_bindings",
        ["block_id", "page_id", "locale"],
    )

    op.create_table(
        "site_block_metrics",
        sa.Column(
            "block_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("site_blocks.id", ondelete="CASCADE"),
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
        sa.Column(
            "range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False
        ),
        sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "impressions", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "clicks", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "conversions", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("revenue", sa.Numeric(14, 4), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'ok'")),
        sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
        sa.Column("top_pages", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_site_block_metrics_range_desc",
        "site_block_metrics",
        ["block_id", "period", "locale", "range_end"],
    )

    op.create_table(
        "site_audit_log",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("snapshot", JSONB, nullable=True),
        sa.Column("actor", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_site_audit_entity",
        "site_audit_log",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_site_audit_created_at", "site_audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_site_audit_created_at", table_name="site_audit_log")
    op.drop_index("ix_site_audit_entity", table_name="site_audit_log")
    op.drop_table("site_audit_log")

    op.drop_index("ix_site_block_metrics_range_desc", table_name="site_block_metrics")
    op.drop_table("site_block_metrics")

    op.drop_index("ix_site_block_bindings_block_page", table_name="site_block_bindings")
    op.drop_table("site_block_bindings")

    op.drop_index("ix_site_page_metrics_range_desc", table_name="site_page_metrics")
    op.drop_table("site_page_metrics")

    op.drop_index(
        "ix_site_block_versions_block_version", table_name="site_block_versions"
    )
    op.drop_table("site_block_versions")

    op.drop_index("ix_site_blocks_template_scope", table_name="site_blocks")
    op.drop_index("ix_site_blocks_scope_section", table_name="site_blocks")
    op.drop_index("ix_site_blocks_scope_status", table_name="site_blocks")
    op.drop_table("site_blocks")

    op.drop_index("ix_site_page_versions_page_version", table_name="site_page_versions")
    op.drop_table("site_page_versions")

    op.drop_table("site_page_drafts")

    op.drop_table("site_block_templates")

    op.drop_index("ix_site_pages_type", table_name="site_pages")
    op.drop_index("ix_site_pages_status", table_name="site_pages")
    op.drop_index("ix_site_pages_slug", table_name="site_pages")
    op.drop_table("site_pages")

    bind = op.get_bind()
    BLOCK_SCOPE_ENUM.drop(bind, checkfirst=True)
    BLOCK_STATUS_ENUM.drop(bind, checkfirst=True)
    PAGE_REVIEW_STATUS_ENUM.drop(bind, checkfirst=True)
    PAGE_STATUS_ENUM.drop(bind, checkfirst=True)
    PAGE_TYPE_ENUM.drop(bind, checkfirst=True)
