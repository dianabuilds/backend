from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import sqlalchemy as sa

from domains.product.site.domain import (
    Block,
    BlockScope,
    BlockStatus,
    BlockTemplate,
    BlockUsage,
    BlockVersion,
    PageReviewStatus,
    PageStatus,
    SiteRepositoryError,
)

from ..tables import (
    SITE_AUDIT_LOG_TABLE,
    SITE_BLOCK_BINDINGS_TABLE,
    SITE_BLOCK_TEMPLATES_TABLE,
    SITE_BLOCK_VERSIONS_TABLE,
    SITE_BLOCKS_TABLE,
    SITE_PAGE_VERSIONS_TABLE,
    SITE_PAGES_TABLE,
)
from . import helpers

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


_TRUE = sa.literal(True)


def _usage_count_subquery() -> sa.ScalarSelect:
    return (
        sa.select(sa.func.count())
        .select_from(SITE_BLOCK_BINDINGS_TABLE)
        .where(
            sa.and_(
                SITE_BLOCK_BINDINGS_TABLE.c.block_id == SITE_BLOCKS_TABLE.c.id,
                SITE_BLOCK_BINDINGS_TABLE.c.active.is_(True),
            )
        )
        .correlate(SITE_BLOCKS_TABLE)
        .scalar_subquery()
    )


def _normalize_scope_filter(
    scope: BlockScope | Sequence[BlockScope] | None,
) -> tuple[str, ...] | None:
    if scope is None:
        return None
    if isinstance(scope, (list, tuple, set)):
        normalized: list[str] = []
        for item in scope:
            if isinstance(item, BlockScope):
                normalized.append(item.value)
            elif item is not None:
                text = str(item).strip()
                if text:
                    normalized.append(text)
        return tuple(dict.fromkeys(normalized))
    if isinstance(scope, BlockScope):
        return (scope.value,)
    text = str(scope).strip()
    return (text,) if text else None


def _normalize_text_filter(
    values: str | Sequence[str] | None,
) -> tuple[str, ...] | None:
    if values is None:
        return None
    if isinstance(values, (list, tuple, set)):
        normalized: list[str] = []
        for item in values:
            text = str(item or "").strip()
            if text:
                normalized.append(text)
        return tuple(dict.fromkeys(normalized))
    text = str(values).strip()
    return (text,) if text else None


class BlockRepositoryMixin:
    if TYPE_CHECKING:

        async def _require_engine(self) -> AsyncEngine: ...
        def _row_to_block(self, row: Mapping[str, Any]) -> Block: ...
        def _row_to_block_version(self, row: Mapping[str, Any]) -> BlockVersion: ...
        def _row_to_block_template(self, row: Mapping[str, Any]) -> BlockTemplate: ...

    # ------------------------------------------------------------------
    # Block templates

    async def list_block_templates(
        self,
        *,
        status: str | Sequence[str] | None = None,
        section: str | None = None,
        query: str | None = None,
    ) -> list[BlockTemplate]:
        engine = await self._require_engine()
        filters: list[Any] = []
        status_filter = _normalize_text_filter(status)
        if status_filter:
            filters.append(SITE_BLOCK_TEMPLATES_TABLE.c.status.in_(status_filter))
        if section:
            filters.append(SITE_BLOCK_TEMPLATES_TABLE.c.section == section)
        if query:
            pattern = f"%{query.lower()}%"
            filters.append(
                sa.or_(
                    sa.func.lower(SITE_BLOCK_TEMPLATES_TABLE.c.title).like(pattern),
                    sa.func.lower(SITE_BLOCK_TEMPLATES_TABLE.c.key).like(pattern),
                    sa.func.lower(SITE_BLOCK_TEMPLATES_TABLE.c.description).like(
                        pattern
                    ),
                )
            )
        stmt = sa.select(SITE_BLOCK_TEMPLATES_TABLE)
        if filters:
            stmt = stmt.where(sa.and_(*filters))
        stmt = stmt.order_by(
            sa.func.lower(SITE_BLOCK_TEMPLATES_TABLE.c.section).asc(),
            sa.func.lower(SITE_BLOCK_TEMPLATES_TABLE.c.title).asc(),
        )
        async with engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        return [self._row_to_block_template(row) for row in rows]

    async def get_block_template(
        self,
        template_id: UUID | None = None,
        *,
        key: str | None = None,
    ) -> BlockTemplate:
        if template_id is None and (key is None or not key.strip()):
            raise SiteRepositoryError("site_block_template_missing_identifier")
        engine = await self._require_engine()
        stmt = sa.select(SITE_BLOCK_TEMPLATES_TABLE).limit(1)
        if template_id is not None:
            stmt = stmt.where(SITE_BLOCK_TEMPLATES_TABLE.c.id == template_id)
        if key:
            stmt = stmt.where(SITE_BLOCK_TEMPLATES_TABLE.c.key == key)
        async with engine.connect() as conn:
            row = (await conn.execute(stmt)).mappings().first()
        if not row:
            raise SiteRepositoryError("site_block_template_not_found")
        return self._row_to_block_template(row)

    async def create_block_template(
        self,
        *,
        key: str,
        title: str,
        section: str,
        description: str | None = None,
        status: str = "available",
        default_locale: str | None = None,
        available_locales: Sequence[str] | None = None,
        block_type: str | None = None,
        category: str | None = None,
        sources: Sequence[str] | None = None,
        surfaces: Sequence[str] | None = None,
        owners: Sequence[str] | None = None,
        catalog_locales: Sequence[str] | None = None,
        documentation_url: str | None = None,
        keywords: Sequence[str] | None = None,
        preview_kind: str | None = None,
        status_note: str | None = None,
        requires_publisher: bool = False,
        allow_shared_scope: bool = True,
        allow_page_scope: bool = True,
        shared_note: str | None = None,
        key_prefix: str | None = None,
        default_data: Mapping[str, Any] | None = None,
        default_meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
    ) -> BlockTemplate:
        engine = await self._require_engine()
        now = helpers.utcnow()
        normalized_default_locale = (default_locale or "ru").strip() or "ru"
        normalized_available = list(helpers.as_locale_list(available_locales))
        if normalized_default_locale not in normalized_available:
            normalized_available.insert(0, normalized_default_locale)
        normalized_sources = list(helpers.as_locale_list(sources))
        normalized_surfaces = list(helpers.as_locale_list(surfaces))
        normalized_owners = list(helpers.as_locale_list(owners))
        normalized_catalog_locales = list(helpers.as_locale_list(catalog_locales))
        normalized_keywords = list(helpers.as_locale_list(keywords))
        sanitized_default_meta = helpers.sanitize_block_meta(default_meta)
        new_id = uuid4()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_BLOCK_TEMPLATES_TABLE.insert().values(
                    id=new_id,
                    key=key,
                    title=title,
                    section=section,
                    description=description,
                    status=status,
                    default_locale=normalized_default_locale,
                    available_locales=normalized_available,
                    block_type=block_type,
                    category=category,
                    sources=normalized_sources or None,
                    surfaces=normalized_surfaces or None,
                    owners=normalized_owners or None,
                    catalog_locales=normalized_catalog_locales or None,
                    documentation_url=documentation_url,
                    keywords=normalized_keywords or None,
                    preview_kind=preview_kind,
                    status_note=status_note,
                    requires_publisher=requires_publisher,
                    allow_shared_scope=allow_shared_scope,
                    allow_page_scope=allow_page_scope,
                    shared_note=shared_note,
                    key_prefix=key_prefix,
                    default_data=dict(default_data or {}),
                    default_meta=sanitized_default_meta,
                    created_at=now,
                    created_by=actor,
                    updated_at=now,
                    updated_by=actor,
                )
            )
        return await self.get_block_template(new_id)

    async def update_block_template(
        self,
        template_id: UUID,
        *,
        title: str | None = None,
        section: str | None = None,
        description: str | None = None,
        status: str | None = None,
        default_locale: str | None = None,
        available_locales: Sequence[str] | None = None,
        block_type: str | None = None,
        category: str | None = None,
        sources: Sequence[str] | None = None,
        surfaces: Sequence[str] | None = None,
        owners: Sequence[str] | None = None,
        catalog_locales: Sequence[str] | None = None,
        documentation_url: str | None = None,
        keywords: Sequence[str] | None = None,
        preview_kind: str | None = None,
        status_note: str | None = None,
        requires_publisher: bool | None = None,
        allow_shared_scope: bool | None = None,
        allow_page_scope: bool | None = None,
        shared_note: str | None = None,
        key_prefix: str | None = None,
        default_data: Mapping[str, Any] | None = None,
        default_meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
    ) -> BlockTemplate:
        engine = await self._require_engine()
        now = helpers.utcnow()
        updates: dict[str, Any] = {
            "updated_at": now,
            "updated_by": actor,
        }
        if title is not None:
            updates["title"] = title
        if section is not None:
            updates["section"] = section
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        if default_locale is not None:
            normalized_default_locale = default_locale.strip() or "ru"
            updates["default_locale"] = normalized_default_locale
        if available_locales is not None:
            normalized_available = list(helpers.as_locale_list(available_locales))
            default_locale_value = updates.get("default_locale")
            if (
                default_locale_value
                and default_locale_value not in normalized_available
            ):
                normalized_available.insert(0, default_locale_value)
            updates["available_locales"] = normalized_available
        if block_type is not None:
            updates["block_type"] = block_type
        if category is not None:
            updates["category"] = category
        if sources is not None:
            updates["sources"] = list(helpers.as_locale_list(sources)) or None
        if surfaces is not None:
            updates["surfaces"] = list(helpers.as_locale_list(surfaces)) or None
        if owners is not None:
            updates["owners"] = list(helpers.as_locale_list(owners)) or None
        if catalog_locales is not None:
            updates["catalog_locales"] = (
                list(helpers.as_locale_list(catalog_locales)) or None
            )
        if documentation_url is not None:
            updates["documentation_url"] = documentation_url
        if keywords is not None:
            updates["keywords"] = list(helpers.as_locale_list(keywords)) or None
        if preview_kind is not None:
            updates["preview_kind"] = preview_kind
        if status_note is not None:
            updates["status_note"] = status_note
        if requires_publisher is not None:
            updates["requires_publisher"] = bool(requires_publisher)
        if allow_shared_scope is not None:
            updates["allow_shared_scope"] = bool(allow_shared_scope)
        if allow_page_scope is not None:
            updates["allow_page_scope"] = bool(allow_page_scope)
        if shared_note is not None:
            updates["shared_note"] = shared_note
        if key_prefix is not None:
            updates["key_prefix"] = key_prefix
        if default_data is not None:
            updates["default_data"] = dict(default_data)
        if default_meta is not None:
            updates["default_meta"] = helpers.sanitize_block_meta(default_meta)
        async with engine.begin() as conn:
            result = await conn.execute(
                SITE_BLOCK_TEMPLATES_TABLE.update()
                .where(SITE_BLOCK_TEMPLATES_TABLE.c.id == template_id)
                .values(**updates)
            )
            if result.rowcount == 0:
                raise SiteRepositoryError("site_block_template_not_found")
        return await self.get_block_template(template_id)

    # ------------------------------------------------------------------
    # Shared blocks CRUD

    async def list_blocks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        scope: BlockScope | Sequence[BlockScope] | None = BlockScope.SHARED,
        section: str | None = None,
        status: BlockStatus | None = None,
        locale: str | None = None,
        query: str | None = None,
        has_draft: bool | None = None,
        requires_publisher: bool | None = None,
        review_status: PageReviewStatus | None = None,
        sort: str = "updated_at_desc",
        is_template: bool | None = None,
        origin_block_id: UUID | None = None,
    ) -> tuple[list[Block], int]:
        engine = await self._require_engine()
        offset = max(page - 1, 0) * page_size

        draft_gt_published = SITE_BLOCKS_TABLE.c.draft_version > sa.func.coalesce(
            SITE_BLOCKS_TABLE.c.published_version, 0
        )
        has_draft_expr = sa.case((draft_gt_published, True), else_=False).label(
            "has_draft"
        )
        usage_count_expr = _usage_count_subquery().label("computed_usage_count")

        filters: list[Any] = []
        scope_values = _normalize_scope_filter(scope)
        if scope_values:
            if len(scope_values) == 1:
                filters.append(SITE_BLOCKS_TABLE.c.scope == scope_values[0])
            else:
                filters.append(SITE_BLOCKS_TABLE.c.scope.in_(scope_values))
        if status:
            filters.append(SITE_BLOCKS_TABLE.c.status == status.value)
        if section:
            filters.append(SITE_BLOCKS_TABLE.c.section == section)
        if locale:
            filters.append(
                sa.or_(
                    SITE_BLOCKS_TABLE.c.default_locale == locale,
                    sa.func.jsonb_exists(SITE_BLOCKS_TABLE.c.available_locales, locale),
                )
            )
        if query:
            pattern = f"%{query.lower()}%"
            filters.append(
                sa.or_(
                    sa.func.lower(SITE_BLOCKS_TABLE.c.title).like(pattern),
                    sa.func.lower(SITE_BLOCKS_TABLE.c.key).like(pattern),
                )
            )
        if has_draft is not None:
            filters.append(has_draft_expr == has_draft)
        if requires_publisher is True:
            filters.append(SITE_BLOCKS_TABLE.c.requires_publisher.is_(True))
        elif requires_publisher is False:
            filters.append(SITE_BLOCKS_TABLE.c.requires_publisher.is_(False))
        if review_status:
            filters.append(SITE_BLOCKS_TABLE.c.review_status == review_status.value)
        if is_template is True:
            filters.append(SITE_BLOCKS_TABLE.c.is_template.is_(True))
        elif is_template is False:
            filters.append(SITE_BLOCKS_TABLE.c.is_template.is_(False))
        if origin_block_id is not None:
            filters.append(SITE_BLOCKS_TABLE.c.origin_block_id == origin_block_id)

        blocks_with_templates = sa.outerjoin(
            SITE_BLOCKS_TABLE,
            SITE_BLOCK_TEMPLATES_TABLE,
            SITE_BLOCKS_TABLE.c.template_id == SITE_BLOCK_TEMPLATES_TABLE.c.id,
        )
        stmt = sa.select(
            SITE_BLOCKS_TABLE,
            SITE_BLOCK_TEMPLATES_TABLE.c.key.label("template_key"),
            usage_count_expr,
            has_draft_expr,
        ).select_from(blocks_with_templates)
        if filters:
            stmt = stmt.where(sa.and_(*filters))

        sort_map: dict[str, sa.ClauseElement] = {
            "updated_at_desc": SITE_BLOCKS_TABLE.c.updated_at.desc(),
            "updated_at_asc": SITE_BLOCKS_TABLE.c.updated_at.asc(),
            "title_asc": sa.func.lower(SITE_BLOCKS_TABLE.c.title).asc(),
            "usage_desc": sa.desc(sa.func.coalesce(usage_count_expr, 0)),
        }
        stmt = (
            stmt.order_by(sort_map.get(sort, sort_map["updated_at_desc"]))
            .limit(page_size)
            .offset(offset)
        )

        count_stmt = sa.select(sa.func.count()).select_from(SITE_BLOCKS_TABLE)
        if filters:
            count_stmt = count_stmt.where(sa.and_(*filters))

        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(count_stmt)
            total = int(total_result.scalar_one())
        return [self._row_to_block(row) for row in rows], total

    async def get_block(
        self,
        block_id: UUID,
        *,
        expected_scope: BlockScope | Sequence[BlockScope] | None = None,
    ) -> Block:
        engine = await self._require_engine()
        blocks_with_templates = sa.outerjoin(
            SITE_BLOCKS_TABLE,
            SITE_BLOCK_TEMPLATES_TABLE,
            SITE_BLOCKS_TABLE.c.template_id == SITE_BLOCK_TEMPLATES_TABLE.c.id,
        )
        stmt = (
            sa.select(
                SITE_BLOCKS_TABLE,
                SITE_BLOCK_TEMPLATES_TABLE.c.key.label("template_key"),
                _usage_count_subquery().label("computed_usage_count"),
            )
            .select_from(blocks_with_templates)
            .where(SITE_BLOCKS_TABLE.c.id == block_id)
            .limit(1)
        )
        scope_filter = _normalize_scope_filter(expected_scope)
        if scope_filter:
            if len(scope_filter) == 1:
                stmt = stmt.where(SITE_BLOCKS_TABLE.c.scope == scope_filter[0])
            else:
                stmt = stmt.where(SITE_BLOCKS_TABLE.c.scope.in_(scope_filter))
        async with engine.connect() as conn:
            row = (await conn.execute(stmt)).mappings().first()
        if not row:
            raise SiteRepositoryError("site_block_not_found")
        return self._row_to_block(row)

    async def save_block(
        self,
        *,
        block_id: UUID,
        payload: Mapping[str, Any],
        meta: Mapping[str, Any],
        version: int | None,
        comment: str | None,
        review_status: PageReviewStatus,
        actor: str | None,
        title: str | None = None,
        section: str | None = None,
        default_locale: str | None = None,
        available_locales: Sequence[str] | None = None,
        requires_publisher: bool | None = None,
        origin_block_id: UUID | None = None,
        is_template: bool | None = None,
    ) -> Block:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.select(SITE_BLOCKS_TABLE.c.draft_version).where(
                    SITE_BLOCKS_TABLE.c.id == block_id
                )
            )
            current_version = result.scalar_one_or_none()
            if current_version is None:
                raise SiteRepositoryError("site_block_not_found")
            if (
                version is not None
                and current_version is not None
                and version != current_version
            ):
                raise SiteRepositoryError("site_block_version_conflict")
            draft_version = (current_version or 0) + 1
            updates: dict[str, Any] = {
                "data": dict(payload),
                "meta": helpers.sanitize_block_meta(meta),
                "comment": comment,
                "review_status": review_status.value,
                "draft_version": draft_version,
                "version": draft_version,
                "updated_at": now,
                "updated_by": actor,
            }
            if title is not None:
                updates["title"] = title
            if section is not None:
                updates["section"] = section
            if default_locale is not None:
                updates["default_locale"] = default_locale
            if available_locales is not None:
                updates["available_locales"] = list(available_locales)
            if requires_publisher is not None:
                updates["requires_publisher"] = requires_publisher
            if origin_block_id is not None:
                updates["origin_block_id"] = origin_block_id
            if is_template is not None:
                updates["is_template"] = is_template
            await conn.execute(
                SITE_BLOCKS_TABLE.update()
                .where(SITE_BLOCKS_TABLE.c.id == block_id)
                .values(**updates)
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="block",
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
        return await self.get_block(block_id)

    async def create_block(
        self,
        *,
        key: str | None,
        title: str | None,
        template_id: UUID | None = None,
        scope: BlockScope,
        section: str,
        default_locale: str | None = None,
        available_locales: Sequence[str] | None = None,
        requires_publisher: bool = False,
        data: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
        is_template: bool = False,
        origin_block_id: UUID | None = None,
    ) -> Block:
        engine = await self._require_engine()
        now = helpers.utcnow()
        new_id = uuid4()
        normalized_default_locale = (default_locale or "ru").strip() or "ru"
        normalized_available = list(helpers.as_locale_list(available_locales))
        if normalized_default_locale not in normalized_available:
            normalized_available.insert(0, normalized_default_locale)
        sanitized_meta = helpers.sanitize_block_meta(meta)
        async with engine.begin() as conn:
            await conn.execute(
                SITE_BLOCKS_TABLE.insert().values(
                    id=new_id,
                    key=key,
                    title=title,
                    template_id=template_id,
                    scope=scope.value,
                    section=section,
                    default_locale=normalized_default_locale,
                    available_locales=normalized_available,
                    status=BlockStatus.DRAFT.value,
                    review_status=PageReviewStatus.NONE.value,
                    data=dict(data or {}),
                    meta=sanitized_meta,
                    updated_at=now,
                    created_at=now,
                    updated_by=actor,
                    draft_version=1,
                    version=1,
                    requires_publisher=requires_publisher,
                    comment=None,
                    is_template=is_template,
                    origin_block_id=origin_block_id,
                )
            )
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="block",
                    entity_id=new_id,
                    action="create",
                    snapshot={
                        "key": key,
                        "title": title,
                        "template_id": str(template_id) if template_id else None,
                        "scope": scope.value,
                        "section": section,
                        "default_locale": normalized_default_locale,
                        "available_locales": normalized_available,
                        "draft_version": 1,
                        "is_template": is_template,
                        "origin_block_id": (
                            str(origin_block_id) if origin_block_id else None
                        ),
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_block(new_id)

    async def publish_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[dict[str, Any]] | None = None,
    ) -> tuple[Block, UUID]:
        engine = await self._require_engine()
        now = helpers.utcnow()
        audit_id = uuid4()
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.select(SITE_BLOCKS_TABLE)
                .where(SITE_BLOCKS_TABLE.c.id == block_id)
                .with_for_update()
            )
            block_row = result.mappings().first()
            if not block_row:
                raise SiteRepositoryError("site_block_not_found")
            block = self._row_to_block(block_row)
            next_version = (block.published_version or 0) + 1

            previous_data: Mapping[str, Any] | None = None
            previous_meta: Mapping[str, Any] | None = None
            if block.published_version:
                previous_stmt = (
                    sa.select(
                        SITE_BLOCK_VERSIONS_TABLE.c.data,
                        SITE_BLOCK_VERSIONS_TABLE.c.meta,
                    )
                    .where(
                        sa.and_(
                            SITE_BLOCK_VERSIONS_TABLE.c.block_id == block_id,
                            SITE_BLOCK_VERSIONS_TABLE.c.version
                            == block.published_version,
                        )
                    )
                    .limit(1)
                )
                prev_result = await conn.execute(previous_stmt)
                prev_row = prev_result.mappings().first()
                if prev_row:
                    previous_data = helpers.as_mapping(prev_row.get("data"))
                    previous_meta = helpers.as_mapping(prev_row.get("meta"))

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
                SITE_BLOCK_VERSIONS_TABLE.insert().values(
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
                SITE_BLOCKS_TABLE.update()
                .where(SITE_BLOCKS_TABLE.c.id == block_id)
                .values(
                    status=BlockStatus.PUBLISHED.value,
                    published_version=next_version,
                    version=next_version,
                    updated_at=now,
                    updated_by=actor,
                    comment=comment,
                    review_status=PageReviewStatus.NONE.value,
                )
            )
            usage_rows = await self._fetch_block_usage_rows(conn, block_id)
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=audit_id,
                    entity_type="block",
                    entity_id=block_id,
                    action="publish",
                    snapshot={
                        "version": next_version,
                        "comment": comment,
                        "diff": diff_to_store,
                        "usage": [
                            {
                                "page_id": str(row["page_id"]),
                                "slug": row["slug"],
                                "title": row["title"],
                                "owner": row.get("owner"),
                                "status": row.get("status"),
                                "section": row["section"],
                            }
                            for row in usage_rows
                        ],
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        block = await self.get_block(block_id)
        return block, audit_id

    # ------------------------------------------------------------------
    # Versions

    async def list_block_history(
        self,
        block_id: UUID,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[BlockVersion], int]:
        engine = await self._require_engine()
        stmt = (
            sa.select(SITE_BLOCK_VERSIONS_TABLE)
            .where(SITE_BLOCK_VERSIONS_TABLE.c.block_id == block_id)
            .order_by(SITE_BLOCK_VERSIONS_TABLE.c.version.desc())
            .limit(limit)
            .offset(offset)
        )
        async with engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
            total_result = await conn.execute(
                sa.select(sa.func.count())
                .select_from(SITE_BLOCK_VERSIONS_TABLE)
                .where(SITE_BLOCK_VERSIONS_TABLE.c.block_id == block_id)
            )
            total = int(total_result.scalar_one())
        return [self._row_to_block_version(row) for row in rows], total

    async def get_block_version(self, block_id: UUID, version: int) -> BlockVersion:
        engine = await self._require_engine()
        stmt = (
            sa.select(SITE_BLOCK_VERSIONS_TABLE)
            .where(
                sa.and_(
                    SITE_BLOCK_VERSIONS_TABLE.c.block_id == block_id,
                    SITE_BLOCK_VERSIONS_TABLE.c.version == version,
                )
            )
            .limit(1)
        )
        async with engine.connect() as conn:
            row = (await conn.execute(stmt)).mappings().first()
        if not row:
            raise SiteRepositoryError("site_block_version_not_found")
        return self._row_to_block_version(row)

    async def restore_block_version(
        self, block_id: UUID, version: int, *, actor: str | None
    ) -> Block:
        current_block = await self.get_block(block_id)
        version_obj = await self.get_block_version(block_id, version)
        expected_version = current_block.draft_version
        restored_block = await self.save_block(
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
                    entity_type="block",
                    entity_id=block_id,
                    action="restore",
                    snapshot={"version": version},
                    actor=actor,
                    created_at=now,
                )
            )
        return restored_block

    # ------------------------------------------------------------------
    # Usage

    async def archive_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        restore: bool = False,
    ) -> Block:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.select(SITE_BLOCKS_TABLE)
                .where(SITE_BLOCKS_TABLE.c.id == block_id)
                .with_for_update()
            )
            row = result.mappings().first()
            if not row:
                raise SiteRepositoryError("site_block_not_found")
            current = self._row_to_block(row)
            target_status = BlockStatus.DRAFT if restore else BlockStatus.ARCHIVED
            if current.status == target_status:
                updated_block = current
            else:
                await conn.execute(
                    SITE_BLOCKS_TABLE.update()
                    .where(SITE_BLOCKS_TABLE.c.id == block_id)
                    .values(
                        status=target_status.value,
                        updated_at=now,
                        updated_by=actor,
                    )
                )
                if not restore:
                    await conn.execute(
                        SITE_BLOCK_BINDINGS_TABLE.update()
                        .where(SITE_BLOCK_BINDINGS_TABLE.c.block_id == block_id)
                        .values(active=False, updated_at=now)
                    )
                await conn.execute(
                    SITE_AUDIT_LOG_TABLE.insert().values(
                        id=uuid4(),
                        entity_type="block",
                        entity_id=block_id,
                        action="restore" if restore else "archive",
                        snapshot={
                            "previous_status": current.status.value,
                            "next_status": target_status.value,
                        },
                        actor=actor,
                        created_at=now,
                    )
                )
                updated_block = None
        if updated_block is None:
            updated_block = await self.get_block(block_id)
        return updated_block

    async def list_block_usage(
        self, block_id: UUID, *, section: str | None = None
    ) -> list[BlockUsage]:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            rows = await self._fetch_block_usage_rows(conn, block_id, section=section)
            return [
                BlockUsage(
                    block_id=row["block_id"],
                    page_id=row["page_id"],
                    section=row["section"],
                    slug=row["slug"],
                    title=row["title"],
                    status=PageStatus(row["status"]),
                    locale=row.get("binding_locale"),
                    has_draft=(row.get("draft_version") or 0)
                    > (row.get("published_version") or 0),
                    last_published_at=row.get("last_published_at"),
                    owner=row.get("owner"),
                )
                for row in rows
            ]

    async def _fetch_block_usage_rows(
        self,
        conn: Any,
        block_id: UUID,
        *,
        section: str | None = None,
    ) -> list[dict[str, Any]]:
        versions_alias = sa.alias(SITE_PAGE_VERSIONS_TABLE, name="pv")
        stmt = (
            sa.select(
                SITE_BLOCK_BINDINGS_TABLE.c.block_id,
                SITE_BLOCK_BINDINGS_TABLE.c.page_id,
                SITE_BLOCK_BINDINGS_TABLE.c.section,
                SITE_BLOCK_BINDINGS_TABLE.c.locale.label("binding_locale"),
                SITE_BLOCK_BINDINGS_TABLE.c.last_published_at,
                SITE_PAGES_TABLE.c.slug,
                SITE_PAGES_TABLE.c.title,
                SITE_PAGES_TABLE.c.status,
                SITE_PAGES_TABLE.c.owner,
                SITE_PAGES_TABLE.c.draft_version,
                SITE_PAGES_TABLE.c.published_version,
                versions_alias.c.published_at.label("page_last_published_at"),
            )
            .join(
                SITE_PAGES_TABLE,
                SITE_PAGES_TABLE.c.id == SITE_BLOCK_BINDINGS_TABLE.c.page_id,
            )
            .outerjoin(
                versions_alias,
                sa.and_(
                    versions_alias.c.page_id == SITE_PAGES_TABLE.c.id,
                    versions_alias.c.version == SITE_PAGES_TABLE.c.published_version,
                ),
            )
            .where(SITE_BLOCK_BINDINGS_TABLE.c.block_id == block_id)
        )
        if section:
            stmt = stmt.where(SITE_BLOCK_BINDINGS_TABLE.c.section == section)
        result = await conn.execute(stmt)
        rows: list[dict[str, Any]] = []
        for row in result.mappings().all():
            last_published_at = row.get("last_published_at") or row.get(
                "page_last_published_at"
            )
            rows.append({**row, "last_published_at": last_published_at})
        return rows


__all__ = ["BlockRepositoryMixin"]
