from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from domains.product.site.domain.models import (
    BlockScope,
    BlockStatus,
    PageReviewStatus,
    PageStatus,
    PageType,
)

metadata = sa.MetaData()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _enum(values: list[str], name: str) -> sa.Enum:
    base = sa.Enum(*values, name=name, native_enum=False, validate_strings=True)
    return base.with_variant(
        pg.ENUM(*values, name=name, create_type=False, validate_strings=True),
        "postgresql",
    )


PAGE_TYPE_ENUM = _enum([member.value for member in PageType], "site_page_type")
PAGE_STATUS_ENUM = _enum([member.value for member in PageStatus], "site_page_status")
REVIEW_STATUS_ENUM = _enum(
    [member.value for member in PageReviewStatus], "site_page_review_status"
)
BLOCK_STATUS_ENUM = _enum(
    [member.value for member in BlockStatus], "site_global_block_status"
)
BLOCK_SCOPE_ENUM = _enum([member.value for member in BlockScope], "site_block_scope")

JSON_TYPE = sa.JSON().with_variant(pg.JSONB(astext_type=sa.Text()), "postgresql")


SITE_PAGES_TABLE = sa.Table(
    "site_pages",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column("slug", sa.Text(), nullable=False, unique=True),
    sa.Column("type", PAGE_TYPE_ENUM, nullable=False),
    sa.Column("status", PAGE_STATUS_ENUM, nullable=False, default=PageStatus.DRAFT),
    sa.Column("title", sa.Text(), nullable=True),
    sa.Column("default_locale", sa.Text(), nullable=False, default="ru"),
    sa.Column("available_locales", JSON_TYPE, nullable=False, default=list),
    sa.Column("slug_localized", JSON_TYPE, nullable=False, default=dict),
    sa.Column("owner", sa.Text(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("published_version", sa.BigInteger(), nullable=True),
    sa.Column("draft_version", sa.BigInteger(), nullable=True),
    sa.Column("has_pending_review", sa.Boolean(), nullable=False, default=False),
    sa.Column("pinned", sa.Boolean(), nullable=False, default=False),
)

sa.Index("ix_site_pages_slug", SITE_PAGES_TABLE.c.slug)
sa.Index("ix_site_pages_status", SITE_PAGES_TABLE.c.status)
sa.Index("ix_site_pages_type", SITE_PAGES_TABLE.c.type)

SITE_PAGE_DRAFTS_TABLE = sa.Table(
    "site_page_drafts",
    metadata,
    sa.Column(
        "page_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_pages.id", ondelete="CASCADE", name="fk_site_page_drafts_page"
        ),
        primary_key=True,
        nullable=False,
    ),
    sa.Column("version", sa.BigInteger(), nullable=False, default=1),
    sa.Column("data", JSON_TYPE, nullable=False, default=dict),
    sa.Column("meta", JSON_TYPE, nullable=False, default=dict),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column(
        "review_status",
        REVIEW_STATUS_ENUM,
        nullable=False,
        default=PageReviewStatus.NONE,
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("updated_by", sa.Text(), nullable=True),
)

SITE_PAGE_VERSIONS_TABLE = sa.Table(
    "site_page_versions",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column(
        "page_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_pages.id", ondelete="CASCADE", name="fk_site_page_versions_page"
        ),
        nullable=False,
    ),
    sa.Column("version", sa.BigInteger(), nullable=False),
    sa.Column("data", JSON_TYPE, nullable=False, default=dict),
    sa.Column("meta", JSON_TYPE, nullable=False, default=dict),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column("diff", JSON_TYPE, nullable=True),
    sa.Column(
        "published_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("published_by", sa.Text(), nullable=True),
)

sa.Index(
    "ix_site_page_versions_page_version",
    SITE_PAGE_VERSIONS_TABLE.c.page_id,
    SITE_PAGE_VERSIONS_TABLE.c.version,
    unique=True,
)

SITE_BLOCKS_TABLE = sa.Table(
    "site_blocks",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column("key", sa.Text(), nullable=True),
    sa.Column("title", sa.Text(), nullable=False),
    sa.Column(
        "template_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_block_templates.id",
            ondelete="SET NULL",
            name="fk_site_blocks_template",
        ),
        nullable=True,
    ),
    sa.Column("scope", BLOCK_SCOPE_ENUM, nullable=False, default=BlockScope.PAGE),
    sa.Column("section", sa.Text(), nullable=False, default="general"),
    sa.Column("default_locale", sa.Text(), nullable=False, default="ru"),
    sa.Column("available_locales", JSON_TYPE, nullable=False, default=list),
    sa.Column("status", BLOCK_STATUS_ENUM, nullable=False, default=BlockStatus.DRAFT),
    sa.Column("is_template", sa.Boolean(), nullable=False, default=False),
    sa.Column(
        "origin_block_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_blocks.id",
            ondelete="SET NULL",
            name="fk_site_blocks_origin_block",
        ),
        nullable=True,
    ),
    sa.Column("version", sa.BigInteger(), nullable=True, default=0),
    sa.Column("data", JSON_TYPE, nullable=False, default=dict),
    sa.Column("meta", JSON_TYPE, nullable=False, default=dict),
    sa.Column(
        "review_status",
        REVIEW_STATUS_ENUM,
        nullable=False,
        default=PageReviewStatus.NONE,
    ),
    sa.Column("published_version", sa.BigInteger(), nullable=True),
    sa.Column("draft_version", sa.BigInteger(), nullable=True),
    sa.Column("requires_publisher", sa.Boolean(), nullable=False, default=False),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("updated_by", sa.Text(), nullable=True),
)

sa.Index(
    "ix_site_blocks_scope_status",
    SITE_BLOCKS_TABLE.c.scope,
    SITE_BLOCKS_TABLE.c.status,
)

sa.Index(
    "ix_site_blocks_scope_section",
    SITE_BLOCKS_TABLE.c.scope,
    SITE_BLOCKS_TABLE.c.section,
)

sa.Index(
    "ix_site_blocks_template_scope",
    SITE_BLOCKS_TABLE.c.template_id,
    SITE_BLOCKS_TABLE.c.scope,
)

sa.Index(
    "ux_site_blocks_key",
    SITE_BLOCKS_TABLE.c.key,
    unique=True,
    postgresql_where=SITE_BLOCKS_TABLE.c.key.isnot(None),  # type: ignore[attr-defined]
)

sa.Index(
    "ix_site_blocks_origin_block",
    SITE_BLOCKS_TABLE.c.origin_block_id,
)

SITE_BLOCK_VERSIONS_TABLE = sa.Table(
    "site_block_versions",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column(
        "block_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_blocks.id", ondelete="CASCADE", name="fk_site_block_versions_block"
        ),
        nullable=False,
    ),
    sa.Column("version", sa.BigInteger(), nullable=False),
    sa.Column("data", JSON_TYPE, nullable=False, default=dict),
    sa.Column("meta", JSON_TYPE, nullable=False, default=dict),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column("diff", JSON_TYPE, nullable=True),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("published_by", sa.Text(), nullable=True),
)

sa.Index(
    "ix_site_block_versions_block_version",
    SITE_BLOCK_VERSIONS_TABLE.c.block_id,
    SITE_BLOCK_VERSIONS_TABLE.c.version,
    unique=True,
)
SITE_BLOCK_TEMPLATES_TABLE = sa.Table(
    "site_block_templates",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column("key", sa.Text(), nullable=False),
    sa.Column("title", sa.Text(), nullable=False),
    sa.Column("section", sa.Text(), nullable=False, default="general"),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("status", sa.Text(), nullable=False, default="available"),
    sa.Column("default_locale", sa.Text(), nullable=False, default="ru"),
    sa.Column("available_locales", JSON_TYPE, nullable=False, default=list),
    sa.Column("default_data", JSON_TYPE, nullable=False, default=dict),
    sa.Column("default_meta", JSON_TYPE, nullable=False, default=dict),
    sa.Column("block_type", sa.Text(), nullable=True),
    sa.Column("category", sa.Text(), nullable=True),
    sa.Column("sources", JSON_TYPE, nullable=True),
    sa.Column("surfaces", JSON_TYPE, nullable=True),
    sa.Column("owners", JSON_TYPE, nullable=True),
    sa.Column("catalog_locales", JSON_TYPE, nullable=True),
    sa.Column("documentation_url", sa.Text(), nullable=True),
    sa.Column("keywords", JSON_TYPE, nullable=True),
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
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("created_by", sa.Text(), nullable=True),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column("updated_by", sa.Text(), nullable=True),
)

sa.Index(
    "ux_site_block_templates_key",
    SITE_BLOCK_TEMPLATES_TABLE.c.key,
    unique=True,
)

SITE_BLOCK_BINDINGS_TABLE = sa.Table(
    "site_block_bindings",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid.uuid4,
    ),
    sa.Column(
        "block_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_blocks.id", ondelete="CASCADE", name="fk_site_block_bindings_block"
        ),
        nullable=False,
    ),
    sa.Column(
        "page_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_pages.id", ondelete="CASCADE", name="fk_site_block_bindings_page"
        ),
        nullable=False,
    ),
    sa.Column("section", sa.Text(), nullable=False),
    sa.Column("locale", sa.Text(), nullable=False),
    sa.Column("position", sa.Integer(), nullable=False, default=0),
    sa.Column("active", sa.Boolean(), nullable=False, default=True),
    sa.Column("has_draft", sa.Boolean(), nullable=False, default=False),
    sa.Column("last_published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
)

sa.Index(
    "ix_site_block_bindings_page_locale",
    SITE_BLOCK_BINDINGS_TABLE.c.page_id,
    SITE_BLOCK_BINDINGS_TABLE.c.locale,
    SITE_BLOCK_BINDINGS_TABLE.c.section,
    SITE_BLOCK_BINDINGS_TABLE.c.position,
)

sa.Index(
    "ix_site_block_bindings_block",
    SITE_BLOCK_BINDINGS_TABLE.c.block_id,
)

SITE_PAGE_METRICS_TABLE = sa.Table(
    "site_page_metrics",
    metadata,
    sa.Column(
        "page_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_pages.id", ondelete="CASCADE", name="fk_site_page_metrics_page"
        ),
        primary_key=True,
        nullable=False,
    ),
    sa.Column("period", sa.Text(), primary_key=True, nullable=False),
    sa.Column("locale", sa.Text(), primary_key=True, nullable=False, default="ru"),
    sa.Column(
        "range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False
    ),
    sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("views", sa.BigInteger(), nullable=False, default=0),
    sa.Column("unique_users", sa.BigInteger(), nullable=False, default=0),
    sa.Column("cta_clicks", sa.BigInteger(), nullable=False, default=0),
    sa.Column("conversions", sa.BigInteger(), nullable=False, default=0),
    sa.Column("avg_time_on_page", sa.Numeric(12, 4), nullable=True),
    sa.Column("bounce_rate", sa.Numeric(7, 4), nullable=True),
    sa.Column("mobile_share", sa.Numeric(7, 4), nullable=True),
    sa.Column("status", sa.Text(), nullable=False, default="ok"),
    sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    ),
)

sa.Index(
    "ix_site_page_metrics_range_desc",
    SITE_PAGE_METRICS_TABLE.c.page_id,
    SITE_PAGE_METRICS_TABLE.c.period,
    SITE_PAGE_METRICS_TABLE.c.locale,
    SITE_PAGE_METRICS_TABLE.c.range_end,
)

SITE_BLOCK_METRICS_TABLE = sa.Table(
    "site_block_metrics",
    metadata,
    sa.Column(
        "block_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "site_blocks.id", ondelete="CASCADE", name="fk_site_block_metrics_block"
        ),
        primary_key=True,
        nullable=False,
    ),
    sa.Column("period", sa.Text(), primary_key=True, nullable=False),
    sa.Column("locale", sa.Text(), primary_key=True, nullable=False, default="ru"),
    sa.Column(
        "range_start", sa.DateTime(timezone=True), primary_key=True, nullable=False
    ),
    sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("impressions", sa.BigInteger(), nullable=False, default=0),
    sa.Column("clicks", sa.BigInteger(), nullable=False, default=0),
    sa.Column("conversions", sa.BigInteger(), nullable=False, default=0),
    sa.Column("revenue", sa.Numeric(14, 4), nullable=True),
    sa.Column("status", sa.Text(), nullable=False, default="ok"),
    sa.Column("source_lag_ms", sa.BigInteger(), nullable=True),
    sa.Column("top_pages", JSON_TYPE, nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    ),
)

sa.Index(
    "ix_site_block_metrics_range_desc",
    SITE_BLOCK_METRICS_TABLE.c.block_id,
    SITE_BLOCK_METRICS_TABLE.c.period,
    SITE_BLOCK_METRICS_TABLE.c.locale,
    SITE_BLOCK_METRICS_TABLE.c.range_end,
)

# ---------------------------------------------------------------------------
# Legacy aliases for compatibility during the migration window.

SITE_GLOBAL_BLOCKS_TABLE = SITE_BLOCKS_TABLE
SITE_GLOBAL_BLOCK_VERSIONS_TABLE = SITE_BLOCK_VERSIONS_TABLE
SITE_GLOBAL_BLOCK_USAGE_TABLE = SITE_BLOCK_BINDINGS_TABLE
SITE_GLOBAL_BLOCK_METRICS_TABLE = SITE_BLOCK_METRICS_TABLE

SITE_AUDIT_LOG_TABLE = sa.Table(
    "site_audit_log",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column("entity_type", sa.Text(), nullable=False),
    sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=False),
    sa.Column("action", sa.Text(), nullable=False),
    sa.Column("snapshot", JSON_TYPE, nullable=True),
    sa.Column("actor", sa.Text(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, default=_utcnow
    ),
)

sa.Index(
    "ix_site_audit_entity",
    SITE_AUDIT_LOG_TABLE.c.entity_type,
    SITE_AUDIT_LOG_TABLE.c.entity_id,
)
sa.Index("ix_site_audit_created_at", SITE_AUDIT_LOG_TABLE.c.created_at)


__all__ = [
    "metadata",
    "SITE_PAGES_TABLE",
    "SITE_PAGE_DRAFTS_TABLE",
    "SITE_PAGE_VERSIONS_TABLE",
    "SITE_BLOCKS_TABLE",
    "SITE_BLOCK_TEMPLATES_TABLE",
    "SITE_BLOCK_VERSIONS_TABLE",
    "SITE_BLOCK_BINDINGS_TABLE",
    "SITE_PAGE_METRICS_TABLE",
    "SITE_BLOCK_METRICS_TABLE",
    "SITE_AUDIT_LOG_TABLE",
    "PAGE_TYPE_ENUM",
    "PAGE_STATUS_ENUM",
    "REVIEW_STATUS_ENUM",
    "BLOCK_STATUS_ENUM",
    "BLOCK_SCOPE_ENUM",
    # Legacy exports maintained for backwards compatibility
    "SITE_GLOBAL_BLOCKS_TABLE",
    "SITE_GLOBAL_BLOCK_VERSIONS_TABLE",
    "SITE_GLOBAL_BLOCK_USAGE_TABLE",
    "SITE_GLOBAL_BLOCK_METRICS_TABLE",
]
