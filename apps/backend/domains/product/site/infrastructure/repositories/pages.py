from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from domains.product.site.domain import (
    BlockBinding,
    BlockScope,
    BlockStatus,
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
    SITE_BLOCK_BINDINGS_TABLE,
    SITE_BLOCKS_TABLE,
    SITE_PAGE_DRAFTS_TABLE,
    SITE_PAGE_VERSIONS_TABLE,
    SITE_PAGES_TABLE,
)
from . import helpers

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    class _RepositoryProtocol(Protocol):
        async def _require_engine(self) -> AsyncEngine: ...
        def _row_to_page(self, row: Mapping[str, Any]) -> Page: ...
        def _row_to_draft(self, row: Mapping[str, Any]) -> PageDraft: ...
        def _row_to_version(self, row: Mapping[str, Any]) -> PageVersion: ...

else:

    class _RepositoryProtocol:  # pragma: no cover - runtime placeholder
        pass


_UNSET: Any = object()


class PageRepositoryMixin(_RepositoryProtocol):

    def _row_to_block_binding(self, row: Mapping[str, Any]) -> BlockBinding:
        available_locales = helpers.as_locale_list(row.get("block_available_locales"))
        extras: dict[str, Any] = {}
        published_version = row.get("block_published_version")
        if published_version is not None:
            extras["published_version"] = int(published_version)
        draft_version = row.get("block_draft_version")
        if draft_version is not None:
            extras["draft_version"] = int(draft_version)
        block_updated_at = row.get("block_updated_at")
        if block_updated_at is not None:
            extras["block_updated_at"] = (
                block_updated_at.isoformat()
                if hasattr(block_updated_at, "isoformat")
                else block_updated_at
            )
        block_updated_by = row.get("block_updated_by")
        if block_updated_by:
            extras["block_updated_by"] = block_updated_by
        extras_payload = extras or None
        scope_raw = row.get("block_scope")
        scope_value = None
        if scope_raw:
            try:
                scope_value = BlockScope(scope_raw)
            except ValueError:
                scope_value = None
        status_raw = row.get("block_status")
        status_value = None
        if status_raw:
            try:
                status_value = BlockStatus(status_raw)
            except ValueError:
                status_value = None
        review_raw = row.get("block_review_status")
        review_value = None
        if review_raw:
            try:
                review_value = PageReviewStatus(review_raw)
            except ValueError:
                review_value = None
        page_status_raw = row.get("page_status")
        page_status_value = None
        if page_status_raw:
            try:
                page_status_value = PageStatus(page_status_raw)
            except ValueError:
                page_status_value = None
        return BlockBinding(
            block_id=row["block_id"],
            page_id=row["page_id"],
            section=row["section"],
            locale=row["locale"],
            has_draft=(
                bool(row.get("has_draft")) if row.get("has_draft") is not None else None
            ),
            last_published_at=row.get("last_published_at"),
            active=bool(row.get("active")) if row.get("active") is not None else None,
            position=row.get("position"),
            title=row.get("block_title"),
            key=row.get("block_key"),
            slug=row.get("page_slug"),
            page_status=page_status_value,
            owner=row.get("page_owner"),
            default_locale=row.get("block_default_locale"),
            available_locales=available_locales if available_locales else None,
            scope=scope_value,
            requires_publisher=row.get("block_requires_publisher"),
            status=status_value,
            review_status=review_value,
            updated_at=row.get("binding_updated_at"),
            extras=extras_payload,
        )

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
        pinned: bool | None = None,
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
            filters.append(
                sa.or_(
                    SITE_PAGES_TABLE.c.default_locale == locale,
                    SITE_PAGES_TABLE.c.available_locales.contains([locale]),
                )
            )
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
        if pinned is True:
            filters.append(SITE_PAGES_TABLE.c.pinned.is_(True))
        elif pinned is False:
            filters.append(SITE_PAGES_TABLE.c.pinned.is_(False))
        if filters:
            stmt = stmt.where(sa.and_(*filters))
        if sort == "updated_at_asc":
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.updated_at.asc())
        elif sort == "title_desc":
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.title.desc())
        elif sort == "title_asc":
            stmt = stmt.order_by(SITE_PAGES_TABLE.c.title.asc())
        elif sort == "pinned_desc":
            stmt = stmt.order_by(
                SITE_PAGES_TABLE.c.pinned.desc(), SITE_PAGES_TABLE.c.updated_at.desc()
            )
        elif sort == "pinned_asc":
            stmt = stmt.order_by(
                SITE_PAGES_TABLE.c.pinned.asc(), SITE_PAGES_TABLE.c.updated_at.desc()
            )
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

    async def _sync_page_block_usage(
        self,
        conn: AsyncConnection,
        *,
        page_id: UUID,
        data: Mapping[str, Any] | None,
        meta: Mapping[str, Any] | None,
    ) -> None:
        data_map = helpers.as_mapping(data)
        meta_map = helpers.as_mapping(meta)
        refs = helpers.extract_shared_block_refs(data_map, meta_map)
        now = helpers.utcnow()
        explicit_meta_keys = {"globalBlocks", "global_blocks", "header", "footer"}
        has_explicit_directive = bool(refs) or any(
            key in meta_map for key in explicit_meta_keys
        )

        existing_rows_result = await conn.execute(
            sa.select(
                SITE_BLOCK_BINDINGS_TABLE.c.id,
                SITE_BLOCK_BINDINGS_TABLE.c.block_id,
                SITE_BLOCK_BINDINGS_TABLE.c.section,
                SITE_BLOCK_BINDINGS_TABLE.c.locale,
                SITE_BLOCK_BINDINGS_TABLE.c.position,
                SITE_BLOCK_BINDINGS_TABLE.c.active,
            ).where(SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id)
        )
        existing_rows = existing_rows_result.mappings().all()
        existing_pair_map: dict[tuple[UUID, str, str | None], Mapping[str, Any]] = {
            (
                row["block_id"],
                row["section"],
                row.get("locale"),
            ): row
            for row in existing_rows
        }

        if not has_explicit_directive:
            if existing_rows:
                await conn.execute(
                    SITE_BLOCK_BINDINGS_TABLE.update()
                    .where(
                        sa.and_(
                            SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id,
                            SITE_BLOCK_BINDINGS_TABLE.c.active.is_(True),
                        )
                    )
                    .values(has_draft=True, updated_at=now)
                )
            return

        page_locale_row = (
            (
                await conn.execute(
                    sa.select(SITE_PAGES_TABLE.c.default_locale).where(
                        SITE_PAGES_TABLE.c.id == page_id
                    )
                )
            )
            .mappings()
            .first()
        )
        page_locale = str((page_locale_row or {}).get("default_locale") or "ru")

        keys = {key for key, _ in refs}
        block_map: dict[str, tuple[UUID, str | None]] = {}
        if keys:
            block_rows_result = await conn.execute(
                sa.select(
                    SITE_BLOCKS_TABLE.c.key,
                    SITE_BLOCKS_TABLE.c.id,
                    SITE_BLOCKS_TABLE.c.section,
                )
                .where(SITE_BLOCKS_TABLE.c.key.in_(keys))
                .where(SITE_BLOCKS_TABLE.c.scope == BlockScope.SHARED.value)
            )
            for row in block_rows_result.mappings():
                block_map[row["key"]] = (row["id"], row.get("section"))

        section_positions: dict[str, int] = {}
        new_pairs: set[tuple[UUID, str, str | None]] = set()
        new_payload: dict[tuple[UUID, str, str | None], dict[str, Any]] = {}
        for key, section_hint in refs:
            block_entry = block_map.get(key)
            if not block_entry:
                continue
            block_id, block_section = block_entry
            section_value = section_hint or block_section or "general"
            section_text = str(section_value).strip() or "general"
            locale_value: str | None = page_locale
            position = section_positions.get(section_text, 0)
            section_positions[section_text] = position + 1
            pair = (block_id, section_text, locale_value)
            if pair in new_pairs:
                continue
            new_pairs.add(pair)
            new_payload[pair] = {
                "block_id": block_id,
                "section": section_text,
                "locale": locale_value,
                "position": position,
            }

        existing_pairs = set(existing_pair_map.keys())
        to_remove = existing_pairs - new_pairs
        to_add = new_pairs - existing_pairs
        to_keep = existing_pairs & new_pairs

        affected_block_ids: set[UUID] = set()

        if to_keep:
            for pair in to_keep:
                row = existing_pair_map[pair]
                payload = new_payload.get(pair)
                update_values: dict[str, Any] = {"has_draft": True, "updated_at": now}
                if payload:
                    current_position = row.get("position") or 0
                    if payload["position"] != current_position:
                        update_values["position"] = payload["position"]
                if not bool(row.get("active", True)):
                    update_values["active"] = True
                await conn.execute(
                    SITE_BLOCK_BINDINGS_TABLE.update()
                    .where(SITE_BLOCK_BINDINGS_TABLE.c.id == row["id"])
                    .values(**update_values)
                )
                affected_block_ids.add(pair[0])

        if to_add:
            await conn.execute(
                SITE_BLOCK_BINDINGS_TABLE.insert(),
                [
                    {
                        "page_id": page_id,
                        "block_id": block_id,
                        "section": section,
                        "locale": locale,
                        "position": new_payload.get(
                            (block_id, section, locale), {}
                        ).get("position", 0),
                        "active": True,
                        "has_draft": True,
                        "last_published_at": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                    for block_id, section, locale in to_add
                ],
            )
            affected_block_ids.update(block_id for block_id, _, _ in to_add)

        if to_remove:
            await conn.execute(
                SITE_BLOCK_BINDINGS_TABLE.delete()
                .where(SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id)
                .where(
                    sa.tuple_(
                        SITE_BLOCK_BINDINGS_TABLE.c.block_id,
                        SITE_BLOCK_BINDINGS_TABLE.c.section,
                        SITE_BLOCK_BINDINGS_TABLE.c.locale,
                    ).in_(list(to_remove))
                )
            )
            affected_block_ids.update(block_id for block_id, _, _ in to_remove)

        # Usage counts are derived dynamically; no table update required.

    async def create_page(
        self,
        *,
        slug: str,
        page_type: PageType,
        title: str,
        locale: str,
        owner: str | None,
        actor: str | None,
        pinned: bool = False,
    ) -> Page:
        engine = await self._require_engine()
        new_id = uuid4()
        now = helpers.utcnow()
        normalized_locale = locale.strip() if isinstance(locale, str) else "ru"
        if not normalized_locale:
            normalized_locale = "ru"
        slug_localized = {normalized_locale: slug}
        async with engine.begin() as conn:
            await conn.execute(
                SITE_PAGES_TABLE.insert().values(
                    id=new_id,
                    slug=slug,
                    type=page_type.value,
                    status=PageStatus.DRAFT.value,
                    title=title,
                    default_locale=normalized_locale,
                    available_locales=[normalized_locale],
                    slug_localized=slug_localized,
                    owner=owner,
                    created_at=now,
                    updated_at=now,
                    draft_version=1,
                    pinned=pinned,
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
                        "locale": normalized_locale,
                        "available_locales": [normalized_locale],
                        "owner": owner,
                        "draft_version": 1,
                        "pinned": pinned,
                    },
                    actor=actor,
                    created_at=now,
                )
            )
        return await self.get_page(new_id)

    async def update_page(
        self,
        *,
        page_id: UUID,
        actor: str | None,
        slug: str | None = _UNSET,
        title: str | None = _UNSET,
        locale: str | None = _UNSET,
        owner: str | None = _UNSET,
        pinned: bool | None = _UNSET,
    ) -> Page:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            current_row = (
                (
                    await conn.execute(
                        sa.select(
                            SITE_PAGES_TABLE.c.slug,
                            SITE_PAGES_TABLE.c.title,
                            SITE_PAGES_TABLE.c.default_locale,
                            SITE_PAGES_TABLE.c.available_locales,
                            SITE_PAGES_TABLE.c.slug_localized,
                            SITE_PAGES_TABLE.c.owner,
                            SITE_PAGES_TABLE.c.pinned,
                        )
                        .where(SITE_PAGES_TABLE.c.id == page_id)
                        .with_for_update()
                    )
                )
                .mappings()
                .first()
            )
            if not current_row:
                raise SitePageNotFound(f"page {page_id} not found")

            current_default_locale = (
                str(current_row.get("default_locale") or "ru").strip() or "ru"
            )
            current_locales = helpers.as_locale_list(
                current_row.get("available_locales")
            )
            if not current_locales:
                current_locales = (current_default_locale,)
            current_slug_map = helpers.as_mapping(current_row.get("slug_localized"))
            if not current_slug_map:
                current_slug_map = {current_default_locale: current_row["slug"]}

            updates: dict[str, Any] = {}
            snapshot_before = {
                "slug": current_row["slug"],
                "title": current_row["title"],
                "default_locale": current_default_locale,
                "available_locales": list(current_locales),
                "owner": current_row.get("owner"),
                "pinned": bool(current_row.get("pinned")),
            }

            if slug is not _UNSET:
                if not isinstance(slug, str) or not slug.strip():
                    raise SiteRepositoryError("site_page_invalid_slug")
                normalized_slug = slug.strip()
                updates["slug"] = normalized_slug
                slug_map_updated = dict(current_slug_map)
                slug_map_updated[current_default_locale] = normalized_slug
                updates["slug_localized"] = slug_map_updated

            if title is not _UNSET:
                if not isinstance(title, str) or not title.strip():
                    raise SiteRepositoryError("site_page_invalid_title")
                updates["title"] = title.strip()

            if locale is not _UNSET:
                if not isinstance(locale, str) or not locale.strip():
                    raise SiteRepositoryError("site_page_invalid_locale")
                normalized_locale = locale.strip()
                updates["default_locale"] = normalized_locale
                locales_ordered = list(
                    dict.fromkeys((normalized_locale, *current_locales))
                )
                updates["available_locales"] = locales_ordered
                slug_map_updated = dict(updates.get("slug_localized", current_slug_map))
                slug_map_updated.setdefault(
                    normalized_locale, updates.get("slug", current_row["slug"])
                )
                updates["slug_localized"] = slug_map_updated

            if owner is not _UNSET:
                if owner is None:
                    updates["owner"] = None
                elif not isinstance(owner, str):
                    raise SiteRepositoryError("site_page_invalid_owner")
                else:
                    updates["owner"] = owner.strip()

            if pinned is not _UNSET:
                if not isinstance(pinned, bool):
                    raise SiteRepositoryError("site_page_invalid_pinned")
                updates["pinned"] = pinned

            if not updates:
                return await self.get_page(page_id)

            updates["updated_at"] = now
            try:
                await conn.execute(
                    SITE_PAGES_TABLE.update()
                    .where(SITE_PAGES_TABLE.c.id == page_id)
                    .values(**updates)
                )
            except IntegrityError as exc:
                raise SiteRepositoryError("site_page_update_conflict") from exc

            audit_snapshot = {
                "changes": {
                    key: value for key, value in updates.items() if key != "updated_at"
                },
                "previous": snapshot_before,
            }
            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=page_id,
                    action="update",
                    snapshot=audit_snapshot,
                    actor=actor,
                    created_at=now,
                )
            )

        return await self.get_page(page_id)

    async def delete_page(self, page_id: UUID, *, actor: str | None = None) -> None:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            page_row = (
                (
                    await conn.execute(
                        sa.select(
                            SITE_PAGES_TABLE.c.id,
                            SITE_PAGES_TABLE.c.slug,
                            SITE_PAGES_TABLE.c.pinned,
                            SITE_PAGES_TABLE.c.title,
                            SITE_PAGES_TABLE.c.default_locale,
                            SITE_PAGES_TABLE.c.available_locales,
                            SITE_PAGES_TABLE.c.owner,
                        )
                        .where(SITE_PAGES_TABLE.c.id == page_id)
                        .with_for_update()
                    )
                )
                .mappings()
                .first()
            )
            if not page_row:
                raise SitePageNotFound(f"page {page_id} not found")

            slug = str(page_row["slug"] or "")
            pinned = bool(page_row["pinned"])
            if pinned or slug in {"/", "main"}:
                raise SiteRepositoryError("site_page_delete_forbidden")

            await conn.execute(
                SITE_AUDIT_LOG_TABLE.insert().values(
                    id=uuid4(),
                    entity_type="page",
                    entity_id=page_id,
                    action="delete",
                    snapshot={
                        "slug": slug,
                        "title": page_row.get("title"),
                        "default_locale": page_row.get("default_locale"),
                        "available_locales": list(
                            helpers.as_locale_list(page_row.get("available_locales"))
                        ),
                        "owner": page_row.get("owner"),
                    },
                    actor=actor,
                    created_at=now,
                )
            )

            await conn.execute(
                SITE_PAGES_TABLE.delete().where(SITE_PAGES_TABLE.c.id == page_id)
            )

    async def get_page(self, page_id: UUID) -> Page:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(SITE_PAGES_TABLE)
                .where(SITE_PAGES_TABLE.c.id == page_id)
                .limit(1)
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
            await self._sync_page_block_usage(
                conn,
                page_id=page_id,
                data=helpers.as_mapping(payload),
                meta=helpers.as_mapping(meta),
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
            await self._sync_page_block_usage(
                conn,
                page_id=page_id,
                data=helpers.as_mapping(draft_obj.data),
                meta=helpers.as_mapping(draft_obj.meta),
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

    async def list_page_global_blocks(
        self, page_id: UUID, *, include_inactive: bool = False
    ) -> list[dict[str, Any]]:
        bindings = await self.list_block_bindings(
            page_id, include_inactive=include_inactive
        )
        blocks: list[dict[str, Any]] = []
        for binding in bindings:
            status_value = binding.status.value if binding.status else None
            if status_value is None and binding.status is not None:
                status_value = str(binding.status)
            review_status_value = (
                binding.review_status.value if binding.review_status else None
            )
            if review_status_value is None and binding.review_status is not None:
                review_status_value = str(binding.review_status)
            extras = binding.extras or {}
            blocks.append(
                {
                    "block_id": str(binding.block_id),
                    "key": binding.key,
                    "title": binding.title,
                    "section": binding.section,
                    "scope": binding.scope.value if binding.scope else "shared",
                    "status": status_value,
                    "default_locale": binding.default_locale,
                    "available_locales": list(binding.available_locales or ()),
                    "requires_publisher": bool(binding.requires_publisher),
                    "published_version": extras.get("published_version"),
                    "draft_version": extras.get("draft_version"),
                    "review_status": review_status_value,
                    "updated_at": extras.get("block_updated_at"),
                    "updated_by": extras.get("block_updated_by"),
                }
            )
        return blocks

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
            raise SitePageVersionNotFound(
                f"version {version} for page {page_id} not found"
            )
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

    def _build_block_bindings_select(self) -> sa.Select[tuple[Any, ...]]:
        return (
            sa.select(
                SITE_BLOCK_BINDINGS_TABLE.c.block_id,
                SITE_BLOCK_BINDINGS_TABLE.c.page_id,
                SITE_BLOCK_BINDINGS_TABLE.c.section,
                SITE_BLOCK_BINDINGS_TABLE.c.locale,
                SITE_BLOCK_BINDINGS_TABLE.c.has_draft,
                SITE_BLOCK_BINDINGS_TABLE.c.last_published_at,
                SITE_BLOCK_BINDINGS_TABLE.c.active,
                SITE_BLOCK_BINDINGS_TABLE.c.position,
                SITE_BLOCK_BINDINGS_TABLE.c.updated_at.label("binding_updated_at"),
                SITE_BLOCKS_TABLE.c.key.label("block_key"),
                SITE_BLOCKS_TABLE.c.title.label("block_title"),
                SITE_BLOCKS_TABLE.c.scope.label("block_scope"),
                SITE_BLOCKS_TABLE.c.status.label("block_status"),
                SITE_BLOCKS_TABLE.c.review_status.label("block_review_status"),
                SITE_BLOCKS_TABLE.c.default_locale.label("block_default_locale"),
                SITE_BLOCKS_TABLE.c.available_locales.label("block_available_locales"),
                SITE_BLOCKS_TABLE.c.requires_publisher.label(
                    "block_requires_publisher"
                ),
                SITE_BLOCKS_TABLE.c.published_version.label("block_published_version"),
                SITE_BLOCKS_TABLE.c.draft_version.label("block_draft_version"),
                SITE_BLOCKS_TABLE.c.updated_at.label("block_updated_at"),
                SITE_BLOCKS_TABLE.c.updated_by.label("block_updated_by"),
                SITE_PAGES_TABLE.c.slug.label("page_slug"),
                SITE_PAGES_TABLE.c.status.label("page_status"),
                SITE_PAGES_TABLE.c.owner.label("page_owner"),
            )
            .select_from(SITE_BLOCK_BINDINGS_TABLE)
            .join(
                SITE_BLOCKS_TABLE,
                SITE_BLOCKS_TABLE.c.id == SITE_BLOCK_BINDINGS_TABLE.c.block_id,
            )
            .join(
                SITE_PAGES_TABLE,
                SITE_PAGES_TABLE.c.id == SITE_BLOCK_BINDINGS_TABLE.c.page_id,
            )
        )

    async def list_block_bindings(
        self,
        page_id: UUID,
        *,
        locale: str | None = None,
        include_inactive: bool = False,
    ) -> list[BlockBinding]:
        engine = await self._require_engine()
        stmt = self._build_block_bindings_select().where(
            SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id
        )
        if locale:
            stmt = stmt.where(SITE_BLOCK_BINDINGS_TABLE.c.locale == locale)
        if not include_inactive:
            stmt = stmt.where(SITE_BLOCK_BINDINGS_TABLE.c.active.is_(True))
        stmt = stmt.order_by(
            SITE_BLOCK_BINDINGS_TABLE.c.section,
            SITE_BLOCK_BINDINGS_TABLE.c.position,
            SITE_BLOCK_BINDINGS_TABLE.c.updated_at.desc(),
        )
        async with engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        return [self._row_to_block_binding(row) for row in rows]

    async def _get_block_binding_row(
        self,
        conn: AsyncConnection,
        *,
        page_id: UUID,
        section: str,
        locale: str,
    ) -> Mapping[str, Any] | None:
        stmt = (
            self._build_block_bindings_select()
            .where(SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id)
            .where(SITE_BLOCK_BINDINGS_TABLE.c.section == section)
            .where(SITE_BLOCK_BINDINGS_TABLE.c.locale == locale)
            .limit(1)
        )
        result = await conn.execute(stmt)
        return result.mappings().first()

    async def upsert_block_binding(
        self,
        page_id: UUID,
        *,
        block_id: UUID,
        section: str,
        locale: str,
    ) -> BlockBinding:
        engine = await self._require_engine()
        normalized_section = section.strip()
        normalized_locale = locale.strip()
        if not normalized_section:
            raise SiteRepositoryError("site_block_binding_invalid_section")
        if not normalized_locale:
            raise SiteRepositoryError("site_block_binding_invalid_locale")
        now = helpers.utcnow()
        async with engine.begin() as conn:
            existing = await conn.execute(
                sa.select(SITE_BLOCK_BINDINGS_TABLE.c.id).where(
                    sa.and_(
                        SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id,
                        SITE_BLOCK_BINDINGS_TABLE.c.section == normalized_section,
                        SITE_BLOCK_BINDINGS_TABLE.c.locale == normalized_locale,
                    )
                )
            )
            row = existing.mappings().first()
            if row:
                await conn.execute(
                    SITE_BLOCK_BINDINGS_TABLE.update()
                    .where(SITE_BLOCK_BINDINGS_TABLE.c.id == row["id"])
                    .values(
                        block_id=block_id,
                        active=True,
                        has_draft=True,
                        updated_at=now,
                    )
                )
            else:
                await conn.execute(
                    SITE_BLOCK_BINDINGS_TABLE.insert().values(
                        block_id=block_id,
                        page_id=page_id,
                        section=normalized_section,
                        locale=normalized_locale,
                        position=0,
                        active=True,
                        has_draft=True,
                        last_published_at=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
            binding_row = await self._get_block_binding_row(
                conn,
                page_id=page_id,
                section=normalized_section,
                locale=normalized_locale,
            )
            if not binding_row:
                raise SiteRepositoryError("site_block_binding_not_found")
            return self._row_to_block_binding(binding_row)

    async def delete_block_binding(
        self,
        page_id: UUID,
        *,
        section: str,
        locale: str,
    ) -> None:
        engine = await self._require_engine()
        normalized_section = section.strip()
        normalized_locale = locale.strip()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_BLOCK_BINDINGS_TABLE.delete().where(
                    sa.and_(
                        SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id,
                        SITE_BLOCK_BINDINGS_TABLE.c.section == normalized_section,
                        SITE_BLOCK_BINDINGS_TABLE.c.locale == normalized_locale,
                    )
                )
            )

    async def mark_block_bindings_published(self, page_id: UUID) -> None:
        engine = await self._require_engine()
        now = helpers.utcnow()
        async with engine.begin() as conn:
            await conn.execute(
                SITE_BLOCK_BINDINGS_TABLE.update()
                .where(SITE_BLOCK_BINDINGS_TABLE.c.page_id == page_id)
                .values(
                    has_draft=False,
                    last_published_at=now,
                    active=True,
                    updated_at=now,
                )
            )

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
