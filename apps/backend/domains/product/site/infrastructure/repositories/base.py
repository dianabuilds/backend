from __future__ import annotations

from collections.abc import Awaitable, Mapping
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.site.domain import (
    GlobalBlock,
    GlobalBlockStatus,
    GlobalBlockVersion,
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
        return Page(
            id=row["id"],
            slug=row["slug"],
            type=PageType(row["type"]),
            status=PageStatus(row["status"]),
            title=row["title"],
            locale=row["locale"],
            owner=row.get("owner"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            published_version=row.get("published_version"),
            draft_version=row.get("draft_version"),
            has_pending_review=bool(row.get("has_pending_review")),
        )

    def _row_to_draft(self, row: Mapping[str, Any]) -> PageDraft:
        return PageDraft(
            page_id=row["page_id"],
            version=int(row["version"]),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            comment=row.get("comment"),
            review_status=PageReviewStatus(row.get("review_status", PageReviewStatus.NONE.value)),
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

    def _row_to_block_version(self, row: Mapping[str, Any]) -> GlobalBlockVersion:
        return GlobalBlockVersion(
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

    def _row_to_block(self, row: Mapping[str, Any]) -> GlobalBlock:
        return GlobalBlock(
            id=row["id"],
            key=row["key"],
            title=row["title"],
            section=row.get("section") or "general",
            locale=row.get("locale"),
            status=GlobalBlockStatus(row["status"]),
            review_status=PageReviewStatus(row.get("review_status", PageReviewStatus.NONE.value)),
            data=helpers.as_mapping(row.get("data")),
            meta=helpers.as_mapping(row.get("meta")),
            updated_at=row["updated_at"],
            updated_by=row.get("updated_by"),
            published_version=row.get("published_version"),
            draft_version=row.get("draft_version"),
            requires_publisher=bool(row.get("requires_publisher")),
            comment=row.get("comment"),
            usage_count=int(row.get("computed_usage_count", row.get("usage_count") or 0) or 0),
        )


__all__ = ["EngineFactory", "SiteRepositoryBase"]
