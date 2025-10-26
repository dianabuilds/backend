from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import sqlalchemy as sa

from domains.product.site.domain import (
    GlobalBlock,
    GlobalBlockStatus,
    GlobalBlockUsage,
    GlobalBlockVersion,
    PageReviewStatus,
    PageStatus,
    SiteRepositoryError,
)

from ..tables import (
    SITE_AUDIT_LOG_TABLE,
    SITE_GLOBAL_BLOCK_USAGE_TABLE,
    SITE_GLOBAL_BLOCK_VERSIONS_TABLE,
    SITE_GLOBAL_BLOCKS_TABLE,
    SITE_PAGE_VERSIONS_TABLE,
    SITE_PAGES_TABLE,
)
from . import helpers

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class GlobalBlockRepositoryMixin:
    if TYPE_CHECKING:

        async def _require_engine(self) -> AsyncEngine: ...
        def _row_to_block(self, row: Mapping[str, Any]) -> GlobalBlock: ...
        def _row_to_block_version(self, row: Mapping[str, Any]) -> GlobalBlockVersion: ...

    async def list_global_blocks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        section: str | None = None,
        status: GlobalBlockStatus | None = None,
        locale: str | None = None,
        query: str | None = None,
        has_draft: bool | None = None,
        sort: str = "updated_at_desc",
    ) -> tuple[list[GlobalBlock], int]:
        engine = await self._require_engine()
        offset = max(page - 1, 0) * page_size

        draft_gt_published = SITE_GLOBAL_BLOCKS_TABLE.c.draft_version > sa.func.coalesce(
            SITE_GLOBAL_BLOCKS_TABLE.c.published_version, 0
        )
        has_draft_expr = sa.case(
            (draft_gt_published, True),
            else_=False,
        ).label("has_draft")
        usage_count_expr = (
            sa.select(sa.func.count())
            .select_from(SITE_GLOBAL_BLOCK_USAGE_TABLE)
            .where(SITE_GLOBAL_BLOCK_USAGE_TABLE.c.block_id == SITE_GLOBAL_BLOCKS_TABLE.c.id)
            .correlate(SITE_GLOBAL_BLOCKS_TABLE)
            .scalar_subquery()
        )

        filters: list[Any] = []
        if status:
            filters.append(SITE_GLOBAL_BLOCKS_TABLE.c.status == status.value)
        if section:
            filters.append(SITE_GLOBAL_BLOCKS_TABLE.c.section == section)
        if locale:
            filters.append(SITE_GLOBAL_BLOCKS_TABLE.c.locale == locale)
        if query:
            pattern = f"%{query.lower()}%"
            filters.append(
                sa.or_(
                    sa.func.lower(SITE_GLOBAL_BLOCKS_TABLE.c.title).like(pattern),
                    sa.func.lower(SITE_GLOBAL_BLOCKS_TABLE.c.key).like(pattern),
                )
            )
        if has_draft is not None:
            filters.append(
                sa.case(
                    (draft_gt_published, True),
                    else_=False,
                )
                == has_draft
            )

        stmt = sa.select(
            SITE_GLOBAL_BLOCKS_TABLE,
            usage_count_expr.label("computed_usage_count"),
            has_draft_expr,
        )
        if filters:
            stmt = stmt.where(sa.and_(*filters))

        sort_map: dict[str, sa.ClauseElement] = {
            "updated_at_desc": SITE_GLOBAL_BLOCKS_TABLE.c.updated_at.desc(),
            "updated_at_asc": SITE_GLOBAL_BLOCKS_TABLE.c.updated_at.asc(),
            "title_asc": sa.func.lower(SITE_GLOBAL_BLOCKS_TABLE.c.title).asc(),
            "usage_desc": sa.desc(sa.func.coalesce(usage_count_expr, 0)),
        }
        sort_clause = sort_map.get(sort, sort_map["updated_at_desc"])
        stmt = stmt.order_by(sort_clause).limit(page_size).offset(offset)

        count_stmt = sa.select(sa.func.count()).select_from(SITE_GLOBAL_BLOCKS_TABLE)
        if filters:
            count_stmt = count_stmt.where(sa.and_(*filters))

        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(count_stmt)
            total = int(total_result.scalar_one())

        blocks = [self._row_to_block(row) for row in rows]
        return blocks, total

    async def get_global_block(self, block_id: UUID) -> GlobalBlock:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(SITE_GLOBAL_BLOCKS_TABLE)
                .where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
                .limit(1)
            )
            row = result.mappings().first()
        if not row:
            raise SiteRepositoryError("site_global_block_not_found")
        return self._row_to_block(row)

    async def save_global_block(
        self,
        *,
        block_id: UUID,
        payload: Mapping[str, Any],
        meta: Mapping[str, Any],
        version: int | None,
        comment: str | None,
        review_status: PageReviewStatus,
        actor: str | None,
    ) -> GlobalBlock:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.select(
                    SITE_GLOBAL_BLOCKS_TABLE.c.draft_version,
                ).where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
            )
            current_version = result.scalar_one_or_none()
            if current_version is None:
                raise SiteRepositoryError("site_global_block_not_found")
            if current_version is not None and version is not None and current_version != version:
                raise SiteRepositoryError("site_global_block_version_conflict")
            draft_version = (current_version or 0) + 1
            await conn.execute(
                SITE_GLOBAL_BLOCKS_TABLE.update()
                .where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
                .values(
                    data=dict(payload),
                    meta=dict(meta),
                    draft_version=draft_version,
                    updated_at=now,
                    updated_by=actor,
                    comment=comment,
                    review_status=review_status.value,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="global_block",
                    entity_id=block_id,
                    action="update",
                    snapshot={
                        "version": draft_version,
                        "review_status": review_status.value,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_global_block(block_id)

    async def create_global_block(
        self,
        *,
        key: str,
        title: str,
        section: str,
        locale: str | None,
        requires_publisher: bool,
        data: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
    ) -> GlobalBlock:
        engine = await self._require_engine()
        now = helpers.utcnow()
        new_id = uuid4()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_GLOBAL_BLOCKS_TABLE.insert().values(
                    id=new_id,
                    key=key,
                    title=title,
                    section=section,
                    locale=locale,
                    status=GlobalBlockStatus.DRAFT.value,
                    review_status=PageReviewStatus.NONE.value,
                    data=dict(data or {}),
                    meta=dict(meta or {}),
                    updated_at=now,
                    updated_by=actor,
                    draft_version=1,
                    requires_publisher=requires_publisher,
                    comment=None,
                    usage_count=0,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="global_block",
                    entity_id=new_id,
                    action="create",
                    snapshot={
                        "key": key,
                        "title": title,
                        "section": section,
                        "locale": locale,
                        "draft_version": 1,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_global_block(new_id)

    async def publish_global_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[dict[str, Any]] | None = None,
    ) -> tuple[GlobalBlock, UUID]:
        engine = await self._require_engine()
        now = helpers.utcnow()
        audit_id = uuid4()
        async with engine.begin() as conn:
            row = await conn.execute(
                sa.select(SITE_GLOBAL_BLOCKS_TABLE)
                .where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
                .with_for_update()
            )
            block_row = row.mappings().first()
            if not block_row:
                raise SiteRepositoryError("site_global_block_not_found")
            block = self._row_to_block(block_row)
            next_version = (block.published_version or 0) + 1
            previous_data: Mapping[str, Any] | None = None
            previous_meta: Mapping[str, Any] | None = None
            if block.published_version:
                previous_stmt = (
                    sa.select(
                        SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.data,
                        SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.meta,
                    )
                    .where(
                        sa.and_(
                            SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.block_id == block_id,
                            SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.version == block.published_version,
                        )
                    )
                    .limit(1)
                )
                previous_result = await conn.execute(previous_stmt)
                previous_row = previous_result.mappings().first()
                if previous_row:
                    previous_data = helpers.as_mapping(previous_row.get("data"))
                    previous_meta = helpers.as_mapping(previous_row.get("meta"))
            computed_diff = diff
            if computed_diff is None:
                computed_diff = helpers.compute_global_block_diff(
                    previous_data,
                    previous_meta,
                    block.data,
                    block.meta,
                )
            diff_to_store = list(computed_diff) if computed_diff else None
            await conn.execute(
                SITE_GLOBAL_BLOCK_VERSIONS_TABLE.insert().values(
                    id=uuid4(),
                    block_id=block_id,
                    version=next_version,
                    data=dict(block.data),
                    meta=dict(block.meta),
                    comment=comment,
                    diff=diff_to_store,
                    published_at=now,
                    published_by=actor,
                )
            )
            await conn.execute(
                SITE_GLOBAL_BLOCKS_TABLE.update()
                .where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
                .values(
                    status=GlobalBlockStatus.PUBLISHED.value,
                    published_version=next_version,
                    updated_at=now,
                    updated_by=actor,
                    comment=comment,
                    review_status=PageReviewStatus.NONE.value,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=audit_id,
                    entity_type="global_block",
                    entity_id=block_id,
                    action="publish",
                    snapshot={"version": next_version, "comment": comment, "diff": diff_to_store},
                    actor=actor,
                    created_at=now,
                )
            )
        block = await self.get_global_block(block_id)
        return block, audit_id

    async def refresh_global_block_usage_count(self, block_id: UUID) -> None:
        engine = await self._require_engine()
        usage_subquery = (
            sa.select(sa.func.count())
            .select_from(SITE_GLOBAL_BLOCK_USAGE_TABLE)
            .where(SITE_GLOBAL_BLOCK_USAGE_TABLE.c.block_id == SITE_GLOBAL_BLOCKS_TABLE.c.id)
            .scalar_subquery()
        )
        async with engine.begin() as conn:
            await conn.execute(
                SITE_GLOBAL_BLOCKS_TABLE.update()
                .where(SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id)
                .values(usage_count=usage_subquery)
            )

    async def list_global_block_history(
        self,
        block_id: UUID,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[GlobalBlockVersion], int]:
        engine = await self._require_engine()
        stmt = (
            sa.select(SITE_GLOBAL_BLOCK_VERSIONS_TABLE)
            .where(SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.block_id == block_id)
            .order_by(SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.version.desc())
            .limit(limit)
            .offset(offset)
        )
        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(
                sa.select(sa.func.count())
                .select_from(SITE_GLOBAL_BLOCK_VERSIONS_TABLE)
                .where(SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.block_id == block_id)
            )
            total = int(total_result.scalar_one())
        return [self._row_to_block_version(row) for row in rows], total

    async def get_global_block_version(self, block_id: UUID, version: int) -> GlobalBlockVersion:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            stmt = (
                sa.select(SITE_GLOBAL_BLOCK_VERSIONS_TABLE)
                .where(
                    sa.and_(
                        SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.block_id == block_id,
                        SITE_GLOBAL_BLOCK_VERSIONS_TABLE.c.version == version,
                    )
                )
                .limit(1)
            )
            result = await conn.execute(stmt)
            row = result.mappings().first()
        if not row:
            raise SiteRepositoryError("site_global_block_version_not_found")
        return self._row_to_block_version(row)

    async def restore_global_block_version(
        self, block_id: UUID, version: int, *, actor: str | None
    ) -> GlobalBlock:
        current_block = await self.get_global_block(block_id)
        version_obj = await self.get_global_block_version(block_id, version)
        expected_version = current_block.draft_version
        restored_block = await self.save_global_block(
            block_id=block_id,
            payload=version_obj.data,
            meta=version_obj.meta,
            version=expected_version,
            comment=f"Restore version {version}",
            review_status=PageReviewStatus.NONE,
            actor=actor,
        )
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="global_block",
                    entity_id=block_id,
                    action="restore",
                    snapshot={"version": version},
                    actor=actor,
                    created_at=now,
                )
            )
        return restored_block

    async def list_block_usage(
        self, block_id: UUID, *, section: str | None = None
    ) -> list[GlobalBlockUsage]:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            versions_alias = sa.alias(SITE_PAGE_VERSIONS_TABLE, name="pv")
            stmt = (
                sa.select(
                    SITE_GLOBAL_BLOCK_USAGE_TABLE,
                    SITE_PAGES_TABLE.c.slug,
                    SITE_PAGES_TABLE.c.title,
                    SITE_PAGES_TABLE.c.status,
                    SITE_PAGES_TABLE.c.locale,
                    SITE_PAGES_TABLE.c.draft_version,
                    SITE_PAGES_TABLE.c.published_version,
                    versions_alias.c.published_at.label("last_published_at"),
                )
                .join(
                    SITE_PAGES_TABLE,
                    SITE_PAGES_TABLE.c.id == SITE_GLOBAL_BLOCK_USAGE_TABLE.c.page_id,
                )
                .outerjoin(
                    versions_alias,
                    sa.and_(
                        versions_alias.c.page_id == SITE_PAGES_TABLE.c.id,
                        versions_alias.c.version == SITE_PAGES_TABLE.c.published_version,
                    ),
                )
            )
            stmt = stmt.where(SITE_GLOBAL_BLOCK_USAGE_TABLE.c.block_id == block_id)
            if section:
                stmt = stmt.where(SITE_GLOBAL_BLOCK_USAGE_TABLE.c.section == section)
            result = await conn.execute(stmt)
            return [
                GlobalBlockUsage(
                    block_id=row["block_id"],
                    page_id=row["page_id"],
                    section=row["section"],
                    slug=row["slug"],
                    title=row["title"],
                    status=PageStatus(row["status"]),
                    locale=row["locale"],
                    has_draft=(row.get("draft_version") or 0) > (row.get("published_version") or 0),
                    last_published_at=row.get("last_published_at"),
                )
                for row in result.mappings().all()
            ]


__all__ = ["GlobalBlockRepositoryMixin"]
