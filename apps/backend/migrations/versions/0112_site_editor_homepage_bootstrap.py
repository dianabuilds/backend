"""Backfill site editor tables with homepage data and pinned flag.

Revision ID: 0112_site_editor_homepage_bootstrap
Revises: 0111_site_editor_tables
Create Date: 2025-10-26
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0112_site_editor_homepage_bootstrap"
down_revision = "0111_site_editor_tables"
branch_labels = None
depends_on = None

METADATA = sa.MetaData()

PAGE_TYPE_ENUM = pg.ENUM(
    "landing",
    "collection",
    "article",
    "system",
    name="site_page_type",
    create_type=False,
)

PAGE_STATUS_ENUM = pg.ENUM(
    "draft",
    "published",
    "archived",
    name="site_page_status",
    create_type=False,
)

REVIEW_STATUS_ENUM = pg.ENUM(
    "none",
    "pending",
    "approved",
    "rejected",
    name="site_page_review_status",
    create_type=False,
)


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    try:
        return any(
            col["name"] == column_name for col in inspector.get_columns(table_name)
        )
    except sa.exc.NoSuchTableError:
        return False


SITE_PAGES_TABLE = sa.Table(
    "site_pages",
    METADATA,
    sa.Column("id", pg.UUID(as_uuid=True)),
    sa.Column("slug", sa.Text()),
    sa.Column("type", PAGE_TYPE_ENUM),
    sa.Column("status", PAGE_STATUS_ENUM),
    sa.Column("title", sa.Text()),
    sa.Column("locale", sa.Text()),
    sa.Column("owner", sa.Text()),
    sa.Column("created_at", sa.DateTime(timezone=True)),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
    sa.Column("published_version", sa.BigInteger()),
    sa.Column("draft_version", sa.BigInteger()),
    sa.Column("has_pending_review", sa.Boolean()),
    sa.Column("pinned", sa.Boolean()),
)

SITE_PAGE_DRAFTS_TABLE = sa.Table(
    "site_page_drafts",
    METADATA,
    sa.Column("page_id", pg.UUID(as_uuid=True)),
    sa.Column("version", sa.BigInteger()),
    sa.Column("data", pg.JSONB(astext_type=sa.Text())),
    sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
    sa.Column("comment", sa.Text()),
    sa.Column("review_status", REVIEW_STATUS_ENUM),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
    sa.Column("updated_by", sa.Text()),
)

SITE_PAGE_VERSIONS_TABLE = sa.Table(
    "site_page_versions",
    METADATA,
    sa.Column("id", pg.UUID(as_uuid=True)),
    sa.Column("page_id", pg.UUID(as_uuid=True)),
    sa.Column("version", sa.BigInteger()),
    sa.Column("data", pg.JSONB(astext_type=sa.Text())),
    sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
    sa.Column("comment", sa.Text()),
    sa.Column("diff", pg.JSONB(astext_type=sa.Text())),
    sa.Column("published_at", sa.DateTime(timezone=True)),
    sa.Column("published_by", sa.Text()),
)

PRODUCT_HOME_CONFIGS_TABLE = sa.Table(
    "product_home_configs",
    METADATA,
    sa.Column("id", pg.UUID(as_uuid=True)),
    sa.Column("slug", sa.Text()),
    sa.Column("version", sa.BigInteger()),
    sa.Column("status", sa.Text()),
    sa.Column("data", pg.JSONB(astext_type=sa.Text())),
    sa.Column("created_by", sa.Text()),
    sa.Column("updated_by", sa.Text()),
    sa.Column("created_at", sa.DateTime(timezone=True)),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
    sa.Column("published_at", sa.DateTime(timezone=True)),
    sa.Column("draft_of", pg.UUID(as_uuid=True)),
)


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    if isinstance(value, list):
        return {"items": value}
    try:
        return dict(value)
    except Exception:
        return {}


def _ensure_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if value is None:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)
    if not _has_column(inspector, "site_pages", "pinned"):
        op.add_column(
            "site_pages",
            sa.Column(
                "pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
        )
        op.create_index("ix_site_pages_pinned", "site_pages", ["pinned"])

    # Bootstrap homepage data ------------------------------------------------
    has_home_config_table = inspector.has_table("product_home_configs")
    if not has_home_config_table:
        # Nothing to migrate; drop default and exit.
        op.alter_column("site_pages", "pinned", server_default=None)
        return

    conn = bind
    homepage_rows = (
        conn.execute(
            sa.select(PRODUCT_HOME_CONFIGS_TABLE).where(
                PRODUCT_HOME_CONFIGS_TABLE.c.slug == "main"
            )
        )
        .mappings()
        .all()
    )
    if not homepage_rows:
        op.alter_column("site_pages", "pinned", server_default=None)
        return

    published_rows = [
        row for row in homepage_rows if str(row.get("status")).lower() == "published"
    ]
    draft_rows = [
        row for row in homepage_rows if str(row.get("status")).lower() == "draft"
    ]

    latest_published = (
        max(published_rows, key=lambda row: int(row.get("version") or 0))
        if published_rows
        else None
    )
    latest_draft = (
        max(
            draft_rows,
            key=lambda row: (
                int(row.get("version") or 0),
                _ensure_datetime(row.get("updated_at")),
            ),
        )
        if draft_rows
        else None
    )
    draft_source = latest_draft or latest_published

    created_at = min(
        (
            _ensure_datetime(row.get("created_at"))
            for row in homepage_rows
            if row.get("created_at")
        ),
        default=datetime.now(UTC),
    )
    updated_at = max(
        (
            _ensure_datetime(
                row.get("updated_at")
                or row.get("published_at")
                or row.get("created_at")
            )
            for row in homepage_rows
        ),
        default=created_at,
    )

    published_version = (
        int(latest_published.get("version"))
        if latest_published and latest_published.get("version")
        else None
    )
    draft_version = (
        int(draft_source.get("version"))
        if draft_source and draft_source.get("version")
        else None
    )

    status = "published" if latest_published else "draft"

    result = conn.execute(
        sa.select(SITE_PAGES_TABLE.c.id)
        .where(SITE_PAGES_TABLE.c.slug == "main")
        .limit(1)
    )
    existing_page_id = result.scalar_one_or_none()
    page_id = existing_page_id or uuid.uuid4()

    page_payload = {
        "id": page_id,
        "slug": "main",
        "type": "landing",
        "status": status,
        "title": "Главная страница",
        "locale": "ru",
        "owner": "marketing",
        "created_at": created_at,
        "updated_at": updated_at,
        "published_version": published_version,
        "draft_version": draft_version,
        "has_pending_review": False,
        "pinned": True,
    }

    if existing_page_id:
        conn.execute(
            SITE_PAGES_TABLE.update()
            .where(SITE_PAGES_TABLE.c.id == page_id)
            .values(**page_payload)
        )
    else:
        conn.execute(SITE_PAGES_TABLE.insert().values(**page_payload))

    if draft_source:
        draft_data = _as_mapping(draft_source.get("data"))
        draft_updated_at = _ensure_datetime(
            draft_source.get("updated_at") or draft_source.get("created_at")
        )
        draft_updated_by = draft_source.get("updated_by") or draft_source.get(
            "created_by"
        )
        existing_draft = conn.execute(
            sa.select(SITE_PAGE_DRAFTS_TABLE.c.page_id)
            .where(SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id)
            .limit(1)
        ).scalar_one_or_none()
        draft_payload = {
            "page_id": page_id,
            "version": draft_version or 1,
            "data": draft_data,
            "meta": {},
            "comment": None,
            "review_status": "none",
            "updated_at": draft_updated_at,
            "updated_by": draft_updated_by,
        }
        if existing_draft:
            conn.execute(
                SITE_PAGE_DRAFTS_TABLE.update()
                .where(SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id)
                .values(**draft_payload)
            )
        else:
            conn.execute(SITE_PAGE_DRAFTS_TABLE.insert().values(**draft_payload))

    existing_versions = conn.execute(
        sa.select(sa.func.count())
        .select_from(SITE_PAGE_VERSIONS_TABLE)
        .where(SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id)
    ).scalar_one()
    if not existing_versions and published_rows:
        for row in sorted(
            published_rows, key=lambda item: int(item.get("version") or 0)
        ):
            version_value = int(row.get("version") or 0)
            if version_value <= 0:
                continue
            published_at = _ensure_datetime(
                row.get("published_at")
                or row.get("updated_at")
                or row.get("created_at")
            )
            published_by = row.get("updated_by") or row.get("created_by")
            conn.execute(
                SITE_PAGE_VERSIONS_TABLE.insert().values(
                    id=uuid.uuid4(),
                    page_id=page_id,
                    version=version_value,
                    data=_as_mapping(row.get("data")),
                    meta={},
                    comment="Migrated from product_home_configs",
                    diff=None,
                    published_at=published_at,
                    published_by=published_by,
                )
            )

    op.alter_column("site_pages", "pinned", server_default=None)


def _page_ids_subquery() -> sa.Select[Any]:
    return sa.select(SITE_PAGES_TABLE.c.id).where(SITE_PAGES_TABLE.c.slug == "main")


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)

    if inspector.has_table("site_pages"):
        subquery = _page_ids_subquery().scalar_subquery()
        if inspector.has_table("site_page_versions"):
            bind.execute(
                SITE_PAGE_VERSIONS_TABLE.delete().where(
                    SITE_PAGE_VERSIONS_TABLE.c.page_id.in_(subquery)
                )
            )
        if inspector.has_table("site_page_drafts"):
            bind.execute(
                SITE_PAGE_DRAFTS_TABLE.delete().where(
                    SITE_PAGE_DRAFTS_TABLE.c.page_id.in_(subquery)
                )
            )
        bind.execute(SITE_PAGES_TABLE.delete().where(SITE_PAGES_TABLE.c.slug == "main"))
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("site_pages")}
        if "ix_site_pages_pinned" in existing_indexes:
            op.drop_index("ix_site_pages_pinned", table_name="site_pages")
        if _has_column(inspector, "site_pages", "pinned"):
            op.drop_column("site_pages", "pinned")
