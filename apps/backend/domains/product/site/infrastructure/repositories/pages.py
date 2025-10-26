from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from domains.product.site.domain import (
    Page,
    PageDraft,
    PageReviewStatus,
    PageStatus,
    PageType,
    PageVersion,
    SitePageNotFound,
    SitePageVersionNotFound,
    SiteRepositoryError,
)

from ..tables import (
    SITE_AUDIT_LOG_TABLE,
    SITE_PAGE_DRAFTS_TABLE,
    SITE_PAGE_VERSIONS_TABLE,
    SITE_PAGES_TABLE,
)
from . import helpers

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class PageRepositoryMixin:
    if TYPE_CHECKING:

        async def _require_engine(self) -> AsyncEngine: ...
        def _row_to_page(self, row: Mapping[str, Any]) -> Page: ...
        def _row_to_draft(self, row: Mapping[str, Any]) -> PageDraft: ...
        def _row_to_version(self, row: Mapping[str, Any]) -> PageVersion: ...

    async def list_pages(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        page_type: PageType | None = None,
        status: PageStatus | None = None,
        locale: str | None = None,
        query: str | None = None,
        has_draft: bool | None = None,
        sort: str = "updated_at_desc",
        allowed_statuses: Collection[PageStatus] | None = None,
        owner_whitelist: Collection[str] | None = None,
        allow_owner_override: bool = False,
    ) -> tuple[list[Page], int]:
        engine = await self._require_engine()
        offset = max(page - 1, 0) * page_size
        filters: list[Any] = []
        stmt = sa.select(SITE_PAGES_TABLE)
        if page_type:
            filters.append(SITE_PAGES_TABLE.c.type == page_type.value)
        if status:
            filters.append(SITE_PAGES_TABLE.c.status == status.value)
        if locale:
            filters.append(SITE_PAGES_TABLE.c.locale == locale)
        if has_draft is True:
            filters.append(SITE_PAGES_TABLE.c.draft_version.is_not(None))
        elif has_draft is False:
            filters.append(SITE_PAGES_TABLE.c.draft_version.is_(None))
        if query:
            like = f"%{query.lower()}%"
            filters.append(
                sa.or_(
                    sa.func.lower(SITE_PAGES_TABLE.c.title).like(like),
                    sa.func.lower(SITE_PAGES_TABLE.c.slug).like(like),
                )
            )
        visibility_clause = self._build_visibility_clause(
            allowed_statuses=allowed_statuses,
            owner_whitelist=owner_whitelist,
            allow_owner_override=allow_owner_override,
        )
        if visibility_clause is not None:
            filters.append(visibility_clause)
        if filters:
            stmt = stmt.where(sa.and_(*filters))
        if sort == "updated_at_asc":
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.updated_at.asc())
        elif sort == "title_asc":
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.title.asc())
        else:
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.updated_at.desc())
        stmt = stmt.limit(page_size).offset(offset)
        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(
                sa.select(sa.func.count())
                .select_from(SITE_PAGES_TABLE)
                .where(sa.and_(*filters) if filters else sa.true())
            )
            total = int(total_result.scalar_one())
        pages = [self._row_to_page(row) for row in rows]
        return pages, total

    def _build_visibility_clause(
        self,
        *,
        allowed_statuses: Collection[PageStatus] | None,
        owner_whitelist: Collection[str] | None,
        allow_owner_override: bool,
    ) -> Any | None:
        status_clause: Any | None = None
        if allowed_statuses is not None:
            status_values = [
                item.value for item in allowed_statuses if isinstance(item, PageStatus)
            ]
            if status_values:
                status_clause = SITE_PAGES_TABLE.c.status.in_(status_values)
        owner_clause: Any | None = None
        if owner_whitelist:
            owners = {
                value.strip()
                for value in owner_whitelist
                if isinstance(value, str) and value.strip()
            }
            if owners:
                owner_clause = SITE_PAGES_TABLE.c.owner.in_(sorted(owners))
        if allow_owner_override and owner_clause is not None:
            if status_clause is not None:
                return sa.or_(status_clause, owner_clause)
            return owner_clause
        return status_clause if status_clause is not None else owner_clause

    async def create_page(
        self,
        *,
        slug: str,
        page_type: PageType,
        title: str,
        locale: str,
        owner: str | None,
        actor: str | None,
    ) -> Page:
        engine = await self._require_engine()
        new_id = uuid4()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_PAGES_TABLE.insert().values(
                    id=new_id,
                    slug=slug,
                    type=page_type.value,
                    status=PageStatus.DRAFT.value,
                    title=title,
                    locale=locale,
                    owner=owner,
                    created_at=now,
                    updated_at=now,
                    draft_version=1,
                )
            )
            await conn.execute(
                SITE_PAGE_DRAFTS_TABLE.insert().values(
                    page_id=new_id,
                    version=1,
                    data={},
                    meta={},
                    comment=None,
                    review_status=PageReviewStatus.NONE.value,
                    updated_at=now,
                    updated_by=actor,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=new_id,
                    action="create",
                    snapshot={
                        "slug": slug,
                        "type": page_type.value,
                        "title": title,
                        "locale": locale,
                        "owner": owner,
                        "draft_version": 1,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_page(new_id)

    async def get_page(self, page_id: UUID) -> Page:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(SITE_PAGES_TABLE).where(SITE_PAGES_TABLE.c.id == page_id).limit(1)
            )
            row = result.mappings().first()
        if not row:
            raise SitePageNotFound(f"page {page_id} not found")
        return self._row_to_page(row)

    async def get_page_draft(self, page_id: UUID) -> PageDraft:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            stmt = (
                sa.select(SITE_PAGE_DRAFTS_TABLE)
                .where(SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id)
                .limit(1)
            )
            result = await conn.execute(stmt)
            row = result.mappings().first()
        if not row:
            raise SitePageNotFound(f"draft for page {page_id} not found")
        return self._row_to_draft(row)

    async def save_page_draft(
        self,
        *,
        page_id: UUID,
        payload: Mapping[str, Any],
        meta: Mapping[str, Any],
        comment: str | None,
        review_status: PageReviewStatus,
        expected_version: int,
        actor: str | None,
    ) -> PageDraft:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.select(SITE_PAGE_DRAFTS_TABLE.c.version).where(
                    SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id
                )
            )
            current_version_row = result.mappings().first()
            if current_version_row:
                current_version = int(current_version_row["version"])
                if current_version != expected_version:
                    raise SiteRepositoryError("site_draft_version_conflict")
                next_version = current_version + 1
                await conn.execute(
                    SITE_PAGE_DRAFTS_TABLE.update()
                    .where(SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id)
                    .values(
                        version=next_version,
                        data=dict(payload),
                        meta=dict(meta),
                        comment=comment,
                        review_status=review_status.value,
                        updated_at=now,
                        updated_by=actor,
                    )
                )
            else:
                next_version = 1
                await conn.execute(
                    SITE_PAGE_DRAFTS_TABLE.insert().values(
                        page_id=page_id,
                        version=next_version,
                        data=dict(payload),
                        meta=dict(meta),
                        comment=comment,
                        review_status=review_status.value,
                        updated_at=now,
                        updated_by=actor,
                    )
                )
            await conn.execute(
                SITE_PAGES_TABLE.update()
                .where(SITE_PAGES_TABLE.c.id == page_id)
                .values(
                    draft_version=next_version,
                    updated_at=now,
                    has_pending_review=review_status
                    in {PageReviewStatus.PENDING, PageReviewStatus.REJECTED},
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=page_id,
                    action="draft_save",
                    snapshot={
                        "version": next_version,
                        "review_status": review_status.value,
                        "comment": comment,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_page_draft(page_id)

    async def publish_page(
        self,
        *,
        page_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[dict[str, Any]] | None = None,
    ) -> PageVersion:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            draft_row = await self._fetch_draft_row(conn, page_id)
            if not draft_row:
                raise SiteRepositoryError("site_draft_missing")
            draft_obj = self._row_to_draft(draft_row)
            result = await conn.execute(
                sa.select(SITE_PAGES_TABLE.c.published_version).where(
                    SITE_PAGES_TABLE.c.id == page_id
                )
            )
            current_version = result.scalar_one_or_none() or 0
            next_version = int(current_version) + 1
            previous_version_data: Mapping[str, Any] | None = None
            previous_version_meta: Mapping[str, Any] | None = None
            if current_version:
                previous_stmt = (
                    sa.select(
                        SITE_PAGE_VERSIONS_TABLE.c.data,
                        SITE_PAGE_VERSIONS_TABLE.c.meta,
                    )
                    .where(
                        sa.and_(
                            SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id,
                            SITE_PAGE_VERSIONS_TABLE.c.version == current_version,
                        )
                    )
                    .limit(1)
                )
                previous_result = await conn.execute(previous_stmt)
                previous_row = previous_result.mappings().first()
                if previous_row:
                    previous_version_data = helpers.as_mapping(previous_row.get("data"))
                    previous_version_meta = helpers.as_mapping(previous_row.get("meta"))
            computed_diff = diff
            if computed_diff is None:
                computed_diff = helpers.compute_page_diff(
                    previous_version_data,
                    previous_version_meta,
                    draft_obj.data,
                    draft_obj.meta,
                )
            diff_to_store = list(computed_diff) if computed_diff else None
            version_id = uuid4()
            await conn.execute(
                SITE_PAGE_VERSIONS_TABLE.insert().values(
                    id=version_id,
                    page_id=page_id,
                    version=next_version,
                    data=dict(draft_obj.data),
                    meta=dict(draft_obj.meta),
                    comment=comment,
                    diff=diff_to_store,
                    published_at=now,
                    published_by=actor,
                )
            )
            await conn.execute(
                SITE_PAGES_TABLE.update()
                .where(SITE_PAGES_TABLE.c.id == page_id)
                .values(
                    status=PageStatus.PUBLISHED.value,
                    published_version=next_version,
                    updated_at=now,
                    has_pending_review=False,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=page_id,
                    action="publish",
                    snapshot={
                        "version": next_version,
                        "comment": comment,
                        "diff": diff_to_store,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_page_version(page_id, next_version)

    async def diff_current_draft(
        self, page_id: UUID
    ) -> tuple[list[dict[str, Any]], int, int | None]:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            draft_row = await self._fetch_draft_row(conn, page_id)
            if not draft_row:
                raise SiteRepositoryError("site_draft_missing")
            draft_version = int(draft_row["version"])
            draft_data = helpers.as_mapping(draft_row.get("data"))
            draft_meta = helpers.as_mapping(draft_row.get("meta"))

            result = await conn.execute(
                sa.select(SITE_PAGES_TABLE.c.published_version).where(
                    SITE_PAGES_TABLE.c.id == page_id
                )
            )
            published_version = result.scalar_one_or_none()
            previous_data: Mapping[str, Any] | None = None
            previous_meta: Mapping[str, Any] | None = None
            if published_version:
                previous_stmt = (
                    sa.select(
                        SITE_PAGE_VERSIONS_TABLE.c.data,
                        SITE_PAGE_VERSIONS_TABLE.c.meta,
                    )
                    .where(
                        sa.and_(
                            SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id,
                            SITE_PAGE_VERSIONS_TABLE.c.version == published_version,
                        )
                    )
                    .limit(1)
                )
                previous_result = await conn.execute(previous_stmt)
                previous_row = previous_result.mappings().first()
                if previous_row:
                    previous_data = helpers.as_mapping(previous_row.get("data"))
                    previous_meta = helpers.as_mapping(previous_row.get("meta"))
            diff = helpers.compute_page_diff(
                previous_data,
                previous_meta,
                draft_data,
                draft_meta,
            )
        published_version_int: int | None
        if published_version is None:
            published_version_int = None
        else:
            try:
                published_version_int = int(published_version)
            except (TypeError, ValueError):
                published_version_int = None
        return diff, draft_version, published_version_int

    async def list_page_history(
        self, page_id: UUID, *, limit: int = 10, offset: int = 0
    ) -> tuple[list[PageVersion], int]:
        engine = await self._require_engine()
        stmt = (
            sa.select(SITE_PAGE_VERSIONS_TABLE)
            .where(SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id)
            .order_by(SITE_PAGE_VERSIONS_TABLE.c.version.desc())
            .limit(limit)
            .offset(offset)
        )
        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(
                sa.select(sa.func.count())
                .select_from(SITE_PAGE_VERSIONS_TABLE)
                .where(SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id)
            )
            total = int(total_result.scalar_one())
        return [self._row_to_version(row) for row in rows], total

    async def get_page_version(self, page_id: UUID, version: int) -> PageVersion:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            stmt = (
                sa.select(SITE_PAGE_VERSIONS_TABLE)
                .where(
                    sa.and_(
                        SITE_PAGE_VERSIONS_TABLE.c.page_id == page_id,
                        SITE_PAGE_VERSIONS_TABLE.c.version == version,
                    )
                )
                .limit(1)
            )
            result = await conn.execute(stmt)
            row = result.mappings().first()
        if not row:
            raise SitePageVersionNotFound(f"version {version} for page {page_id} not found")
        return self._row_to_version(row)

    async def restore_page_version(
        self, page_id: UUID, version: int, *, actor: str | None
    ) -> PageDraft:
        version_obj = await self.get_page_version(page_id, version)
        draft = await self.save_page_draft(
            page_id=page_id,
            payload=version_obj.data,
            meta=version_obj.meta,
            comment=f"Restore version {version}",
            review_status=PageReviewStatus.NONE,
            expected_version=await self._get_current_draft_version(page_id),
            actor=actor,
        )
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=page_id,
                    action="restore",
                    snapshot={"version": version},
                    actor=actor,
                    created_at=now,
                )
            )
        return draft

    async def _get_current_draft_version(self, page_id: UUID) -> int:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(SITE_PAGE_DRAFTS_TABLE.c.version).where(
                    SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id
                )
            )
            row = result.scalar_one_or_none()
        if row is None:
            return 0
        return int(row)

    async def _fetch_draft_row(
        self, conn: AsyncConnection, page_id: UUID
    ) -> Mapping[str, Any] | None:
        result = await conn.execute(
            sa.select(SITE_PAGE_DRAFTS_TABLE)
            .where(SITE_PAGE_DRAFTS_TABLE.c.page_id == page_id)
            .limit(1)
        )
        return result.mappings().first()


__all__ = ["PageRepositoryMixin"]
