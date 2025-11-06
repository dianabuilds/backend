from __future__ import annotations

from collections.abc import Awaitable, Mapping
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.site.domain import (
    Block,
    BlockScope,
    BlockStatus,
    BlockTemplate,
    BlockVersion,
    Page,
    PageDraft,
    PageReviewStatus,
    PageStatus,
    PageType,
    PageVersion,
    SiteRepositoryError,
)

from . import helpers


class EngineFactory(Protocol):
    def __call__(self) -> Awaitable[AsyncEngine | None]: ...


class SiteRepositoryBase:
    def __init__(self, engine_factory: EngineFactory) -> None:
        self._engine_factory = engine_factory

    async def _require_engine(self) -> AsyncEngine:
        engine = await self._engine_factory()
        if engine is None:
            raise SiteRepositoryError("site_engine_unavailable")
        return engine

    # Conversion helpers -----------------------------------------------------

    def _row_to_page(self, row: Mapping[str, Any]) -> Page:
        default_locale = str(row.get("default_locale") or "ru")
        available_locales = helpers.as_locale_list(row.get("available_locales"))
        if not available_locales:
            available_locales = (default_locale,)
        slug_localized = (
            helpers.as_mapping(row.get("slug_localized"))
            if row.get("slug_localized")
            else None
        )
        locale = row.get("locale") or default_locale
        return Page(
            id=row["id"],
            slug=row["slug"],
            type=PageType(row["type"]),
            status=PageStatus(row["status"]),
            title=row["title"],
            default_locale=default_locale,
            owner=row.get("owner"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            published_version=row.get("published_version"),
            draft_version=row.get("draft_version"),
            has_pending_review=bool(row.get("has_pending_review")),
            pinned=bool(row.get("pinned")),
            available_locales=available_locales,
            slug_localized=slug_localized,
            locale=locale,
        )

    def _row_to_draft(self, row: Mapping[str, Any]) -> PageDraft:
        return PageDraft(
            page_id=row["page_id"],
            version=int(row["version"]),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            comment=row.get("comment"),
            review_status=PageReviewStatus(
                row.get("review_status", PageReviewStatus.NONE.value)
            ),
            updated_at=row["updated_at"],
            updated_by=row.get("updated_by"),
        )

    def _row_to_version(self, row: Mapping[str, Any]) -> PageVersion:
        return PageVersion(
            id=row["id"],
            page_id=row["page_id"],
            version=int(row["version"]),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            comment=row.get("comment"),
            diff=helpers.as_list_of_mapping(row.get("diff")),
            published_at=row["published_at"],
            published_by=row.get("published_by"),
        )

    def _row_to_block_version(self, row: Mapping[str, Any]) -> BlockVersion:
        return BlockVersion(
            id=row["id"],
            block_id=row["block_id"],
            version=int(row["version"]),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            comment=row.get("comment"),
            diff=helpers.as_list_of_mapping(row.get("diff")),
            published_at=row["published_at"],
            published_by=row.get("published_by"),
        )

    def _row_to_block(self, row: Mapping[str, Any]) -> Block:
        default_locale = str(row.get("default_locale") or "ru")
        available_locales = helpers.as_locale_list(row.get("available_locales"))
        if not available_locales:
            available_locales = (default_locale,)
        extras_payload = row.get("extras")
        extras = helpers.as_mapping(extras_payload) if extras_payload else None
        scope_raw = row.get("scope") or BlockScope.SHARED.value
        try:
            scope = BlockScope(scope_raw)
        except ValueError:
            scope = BlockScope.SHARED
        usage_count = row.get("computed_usage_count")
        version = row.get("version")
        if version is None:
            version = row.get("draft_version") or row.get("published_version")
        return Block(
            id=row["id"],
            key=row.get("key"),
            title=row.get("title"),
            template_id=row.get("template_id"),
            template_key=row.get("template_key"),
            section=row.get("section") or "general",
            scope=scope,
            default_locale=default_locale,
            available_locales=available_locales,
            status=BlockStatus(row["status"]),
            review_status=PageReviewStatus(
                row.get("review_status", PageReviewStatus.NONE.value)
            ),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            updated_at=row["updated_at"],
            updated_by=row.get("updated_by"),
            published_version=row.get("published_version"),
            draft_version=row.get("draft_version"),
            requires_publisher=bool(row.get("requires_publisher")),
            comment=row.get("comment"),
            usage_count=int(usage_count or 0),
            extras=extras,
            locale=row.get("locale") or default_locale,
            created_at=row.get("created_at"),
            updated_by_id=row.get("updated_by_id"),
            version=version,
            has_pending_publish=bool(
                (row.get("draft_version") or 0) > (row.get("published_version") or 0)
            ),
            source=row.get("source"),
            is_template=bool(row.get("is_template")),
            origin_block_id=row.get("origin_block_id"),
        )

    def _row_to_block_template(self, row: Mapping[str, Any]) -> BlockTemplate:
        default_locale = str(row.get("default_locale") or "ru")
        available_locales = helpers.as_locale_list(row.get("available_locales"))
        if not available_locales:
            available_locales = (default_locale,)
        sources = helpers.as_locale_list(row.get("sources"))
        surfaces = helpers.as_locale_list(row.get("surfaces"))
        owners = helpers.as_locale_list(row.get("owners"))
        catalog_locales = helpers.as_locale_list(row.get("catalog_locales"))
        keywords = helpers.as_locale_list(row.get("keywords"))
        return BlockTemplate(
            id=row["id"],
            key=row["key"],
            title=row["title"],
            section=row.get("section") or "general",
            description=row.get("description"),
            status=row.get("status") or "available",
            default_locale=default_locale,
            available_locales=available_locales,
            default_data=helpers.as_mapping(row.get("default_data")),
            default_meta=helpers.as_mapping(row.get("default_meta")),
            block_type=row.get("block_type"),
            category=row.get("category"),
            sources=sources,
            surfaces=surfaces,
            owners=owners,
            catalog_locales=catalog_locales,
            documentation_url=row.get("documentation_url"),
            keywords=keywords,
            preview_kind=row.get("preview_kind"),
            status_note=row.get("status_note"),
            requires_publisher=bool(row.get("requires_publisher")),
            allow_shared_scope=bool(row.get("allow_shared_scope", True)),
            allow_page_scope=bool(row.get("allow_page_scope", True)),
            shared_note=row.get("shared_note"),
            key_prefix=row.get("key_prefix"),
            created_at=row.get("created_at"),
            created_by=row.get("created_by"),
            updated_at=row.get("updated_at"),
            updated_by=row.get("updated_by"),
        )


__all__ = ["EngineFactory", "SiteRepositoryBase"]
