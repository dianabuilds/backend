from __future__ import annotations

import logging
from collections.abc import Collection, Mapping
from typing import Any
from uuid import UUID

from domains.platform.notifications.application.interactors.commands import (
    NotificationCreateCommand,
)
from domains.platform.worker.application.service import (
    JobCreateCommand,
    WorkerQueueService,
)
from domains.platform.worker.domain.models import WorkerJob
from domains.product.site.domain import (
    Block,
    BlockBinding,
    BlockMetrics,
    BlockScope,
    BlockStatus,
    BlockTemplate,
    BlockUsage,
    BlockVersion,
    Page,
    PageDraft,
    PageMetrics,
    PageReviewStatus,
    PageStatus,
    PageType,
    PageVersion,
)
from domains.product.site.infrastructure import SiteRepository

from .validation import PageDraftValidator, ValidatedDraft

logger = logging.getLogger(__name__)
_UNSET: Any = object()


class SiteService:
    """Application facade for site editor use cases."""

    def __init__(
        self,
        repository: SiteRepository,
        validator: PageDraftValidator | None = None,
        worker_queue: WorkerQueueService | None = None,
        notify_service: Any | None = None,
    ) -> None:
        self._repo = repository
        self._validator = validator or PageDraftValidator()
        self._worker_queue = worker_queue
        self._notify_service = notify_service

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
        viewer_roles: Collection[str] | None = None,
        viewer_team: str | None = None,
        viewer_id: str | None = None,
    ) -> tuple[list[Page], int]:
        allow_owner_override = False
        allowed_statuses: set[PageStatus] | None = None
        owner_whitelist: set[str] | None = None
        if viewer_roles is not None:
            normalized_roles = {
                role.strip().lower()
                for role in viewer_roles
                if isinstance(role, str) and role.strip()
            }
            elevated_roles = {
                "editor",
                "moderator",
                "admin",
            }
            if normalized_roles.isdisjoint(elevated_roles):
                allow_owner_override = True
                allowed_statuses = {PageStatus.PUBLISHED}
                owner_candidates = {
                    value.strip()
                    for value in (viewer_team or "", viewer_id or "")
                    if isinstance(value, str) and value.strip()
                }
                owner_whitelist = owner_candidates or None
        return await self._repo.list_pages(
            page=page,
            page_size=page_size,
            page_type=page_type,
            status=status,
            locale=locale,
            query=query,
            has_draft=has_draft,
            sort=sort,
            pinned=pinned,
            allowed_statuses=allowed_statuses,
            owner_whitelist=owner_whitelist,
            allow_owner_override=allow_owner_override,
        )

    async def create_page(
        self,
        *,
        slug: str,
        page_type: PageType,
        title: str,
        locale: str,
        owner: str | None,
        actor: str | None = None,
        pinned: bool = False,
    ) -> Page:
        return await self._repo.create_page(
            slug=slug,
            page_type=page_type,
            title=title,
            locale=locale,
            owner=owner,
            actor=actor,
            pinned=pinned,
        )

    async def delete_page(self, page_id: UUID, *, actor: str | None = None) -> None:
        await self._repo.delete_page(page_id=page_id, actor=actor)

    async def update_page(
        self,
        page_id: UUID,
        *,
        slug: str | None = _UNSET,
        title: str | None = _UNSET,
        locale: str | None = _UNSET,
        owner: str | None = _UNSET,
        pinned: bool | None = _UNSET,
        actor: str | None = None,
    ) -> Page:
        updates: dict[str, Any] = {}
        if slug is not _UNSET:
            updates["slug"] = slug
        if title is not _UNSET:
            updates["title"] = title
        if locale is not _UNSET:
            updates["locale"] = locale
        if owner is not _UNSET:
            updates["owner"] = owner
        if pinned is not _UNSET:
            updates["pinned"] = pinned
        if not updates:
            return await self.get_page(page_id)
        return await self._repo.update_page(
            page_id=page_id,
            actor=actor,
            **updates,
        )

    async def get_page(self, page_id: UUID) -> Page:
        return await self._repo.get_page(page_id)

    async def get_page_draft(self, page_id: UUID) -> PageDraft:
        return await self._repo.get_page_draft(page_id)

    async def list_page_shared_bindings(
        self,
        page_id: UUID,
        *,
        locale: str | None = None,
        include_inactive: bool = False,
    ) -> list[BlockBinding]:
        return await self._repo.list_block_bindings(
            page_id,
            locale=locale,
            include_inactive=include_inactive,
        )

    async def assign_shared_block(
        self,
        page_id: UUID,
        *,
        section: str,
        block_id: UUID,
        locale: str | None = None,
    ) -> BlockBinding:
        target_locale = locale
        if not target_locale:
            page = await self.get_page(page_id)
            target_locale = page.default_locale or page.locale or "ru"
        return await self._repo.upsert_block_binding(
            page_id,
            block_id=block_id,
            section=section,
            locale=target_locale,
        )

    async def remove_shared_block(
        self,
        page_id: UUID,
        *,
        section: str,
        locale: str | None = None,
    ) -> None:
        target_locale = locale
        if not target_locale:
            page = await self.get_page(page_id)
            target_locale = page.default_locale or page.locale or "ru"
        await self._repo.delete_block_binding(
            page_id,
            section=section,
            locale=target_locale,
        )

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
        validated = self._validator.validate(payload, meta)
        return await self._repo.save_page_draft(
            page_id=page_id,
            payload=validated.data,
            meta=validated.meta,
            comment=comment,
            review_status=review_status,
            expected_version=expected_version,
            actor=actor,
        )

    async def publish_page(
        self,
        *,
        page_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[Mapping[str, Any]] | None = None,
    ) -> PageVersion:
        draft = await self._repo.get_page_draft(page_id)
        # Ensure the latest draft satisfies validation before publishing.
        self._validator.validate(draft.data, draft.meta)
        version = await self._repo.publish_page(
            page_id=page_id,
            actor=actor,
            comment=comment,
            diff=diff,
        )
        await self._repo.mark_block_bindings_published(page_id)
        return version

    async def list_page_history(
        self, page_id: UUID, *, limit: int = 10, offset: int = 0
    ) -> tuple[list[PageVersion], int]:
        return await self._repo.list_page_history(page_id, limit=limit, offset=offset)

    async def diff_page_draft(
        self, page_id: UUID
    ) -> tuple[list[Mapping[str, Any]], int, int | None]:
        return await self._repo.diff_current_draft(page_id)

    async def get_page_version(self, page_id: UUID, version: int) -> PageVersion:
        return await self._repo.get_page_version(page_id, version)

    async def restore_page_version(
        self, page_id: UUID, version: int, *, actor: str | None
    ) -> PageDraft:
        return await self._repo.restore_page_version(page_id, version, actor=actor)

    async def list_page_global_blocks(
        self, page_id: UUID, *, include_inactive: bool = False
    ) -> list[Mapping[str, Any]]:
        return await self._repo.list_page_global_blocks(
            page_id, include_inactive=include_inactive
        )

    async def get_page_metrics(
        self, page_id: UUID, *, period: str = "7d", locale: str = "ru"
    ) -> PageMetrics | None:
        return await self._repo.get_page_metrics(page_id, period=period, locale=locale)

    def validate_draft_payload(
        self,
        *,
        payload: Mapping[str, Any] | None,
        meta: Mapping[str, Any] | None,
    ) -> ValidatedDraft:
        return self._validator.validate(payload, meta)

    async def list_block_templates(
        self,
        *,
        status: str | Collection[str] | None = None,
        section: str | None = None,
        query: str | None = None,
    ) -> list[BlockTemplate]:
        return await self._repo.list_block_templates(
            status=status,
            section=section,
            query=query,
        )

    async def get_block_template(
        self,
        template_id: UUID | None = None,
        *,
        key: str | None = None,
    ) -> BlockTemplate:
        return await self._repo.get_block_template(template_id, key=key)

    async def list_blocks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        scope: BlockScope | Collection[BlockScope] | None = None,
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
        return await self._repo.list_blocks(
            page=page,
            page_size=page_size,
            scope=scope,
            section=section,
            status=status,
            locale=locale,
            query=query,
            has_draft=has_draft,
            requires_publisher=requires_publisher,
            review_status=review_status,
            sort=sort,
            is_template=is_template,
            origin_block_id=origin_block_id,
        )

    async def get_block(
        self,
        block_id: UUID,
        *,
        expected_scope: BlockScope | Collection[BlockScope] | None = None,
    ) -> Block:
        return await self._repo.get_block(
            block_id,
            expected_scope=expected_scope,
        )

    async def list_global_blocks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        section: str | None = None,
        status: BlockStatus | None = None,
        locale: str | None = None,
        query: str | None = None,
        has_draft: bool | None = None,
        requires_publisher: bool | None = None,
        review_status: PageReviewStatus | None = None,
        sort: str = "updated_at_desc",
    ) -> tuple[list[Block], int]:
        return await self.list_blocks(
            page=page,
            page_size=page_size,
            scope=BlockScope.SHARED,
            section=section,
            status=status,
            locale=locale,
            query=query,
            has_draft=has_draft,
            requires_publisher=requires_publisher,
            review_status=review_status,
            sort=sort,
        )

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
        available_locales: Collection[str] | None = None,
        requires_publisher: bool | None = None,
    ) -> Block:
        return await self._repo.save_block(
            block_id=block_id,
            payload=payload,
            meta=meta,
            version=version,
            comment=comment,
            review_status=review_status,
            actor=actor,
            title=title,
            section=section,
            default_locale=default_locale,
            available_locales=available_locales,
            requires_publisher=requires_publisher,
        )

    async def get_global_block(self, block_id: UUID) -> Block:
        return await self.get_block(block_id, expected_scope=BlockScope.SHARED)

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
        title: str | None = None,
        section: str | None = None,
        default_locale: str | None = None,
        available_locales: Collection[str] | None = None,
        requires_publisher: bool | None = None,
    ) -> Block:
        return await self.save_block(
            block_id=block_id,
            payload=payload,
            meta=meta,
            version=version,
            comment=comment,
            review_status=review_status,
            actor=actor,
            title=title,
            section=section,
            default_locale=default_locale,
            available_locales=available_locales,
            requires_publisher=requires_publisher,
        )

    async def publish_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[Mapping[str, Any]] | None = None,
    ) -> tuple[Block, UUID, list[BlockUsage], list[WorkerJob]]:
        block, audit_id = await self._repo.publish_block(
            block_id=block_id,
            actor=actor,
            comment=comment,
            diff=diff,
        )
        usage = await self._repo.list_block_usage(block_id)
        jobs = await self._enqueue_page_republish_jobs(block_id, usage)
        refreshed_block = await self._repo.get_block(block_id)
        await self._notify_block_publish(
            refreshed_block,
            usage,
            audit_id=audit_id,
            actor=actor,
        )
        return refreshed_block, audit_id, usage, jobs

    async def publish_global_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[Mapping[str, Any]] | None = None,
    ) -> tuple[Block, UUID, list[BlockUsage], list[WorkerJob]]:
        return await self.publish_block(
            block_id=block_id,
            actor=actor,
            comment=comment,
            diff=diff,
        )

    async def archive_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        restore: bool = False,
    ) -> tuple[Block, list[BlockUsage]]:
        block = await self._repo.archive_block(
            block_id=block_id,
            actor=actor,
            restore=restore,
        )
        usage = await self._repo.list_block_usage(block_id)
        return block, usage

    async def archive_global_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        restore: bool = False,
    ) -> tuple[Block, list[BlockUsage]]:
        return await self.archive_block(block_id=block_id, actor=actor, restore=restore)

    async def create_block(
        self,
        *,
        key: str | None,
        title: str | None,
        template_id: UUID | None = None,
        template_key: str | None = None,
        section: str,
        scope: BlockScope,
        default_locale: str | None = None,
        available_locales: Collection[str] | None = None,
        requires_publisher: bool = False,
        data: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
        is_template: bool = False,
        origin_block_id: UUID | None = None,
    ) -> Block:
        resolved_template_id = template_id
        if resolved_template_id is None and template_key:
            template = await self._repo.get_block_template(key=template_key)
            resolved_template_id = template.id
        return await self._repo.create_block(
            key=key,
            title=title,
            template_id=resolved_template_id,
            scope=scope,
            section=section,
            default_locale=default_locale,
            available_locales=(
                list(available_locales) if available_locales is not None else None
            ),
            requires_publisher=requires_publisher,
            data=data,
            meta=meta,
            actor=actor,
            is_template=is_template,
            origin_block_id=origin_block_id,
        )

    async def create_block_template(
        self,
        *,
        key: str,
        title: str,
        section: str,
        description: str | None = None,
        status: str = "available",
        default_locale: str | None = None,
        available_locales: Collection[str] | None = None,
        block_type: str | None = None,
        category: str | None = None,
        sources: Collection[str] | None = None,
        surfaces: Collection[str] | None = None,
        owners: Collection[str] | None = None,
        catalog_locales: Collection[str] | None = None,
        documentation_url: str | None = None,
        keywords: Collection[str] | None = None,
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
        return await self._repo.create_block_template(
            key=key,
            title=title,
            section=section,
            description=description,
            status=status,
            default_locale=default_locale,
            available_locales=(
                list(available_locales) if available_locales is not None else None
            ),
            block_type=block_type,
            category=category,
            sources=list(sources) if sources is not None else None,
            surfaces=list(surfaces) if surfaces is not None else None,
            owners=list(owners) if owners is not None else None,
            catalog_locales=(
                list(catalog_locales) if catalog_locales is not None else None
            ),
            documentation_url=documentation_url,
            keywords=list(keywords) if keywords is not None else None,
            preview_kind=preview_kind,
            status_note=status_note,
            requires_publisher=requires_publisher,
            allow_shared_scope=allow_shared_scope,
            allow_page_scope=allow_page_scope,
            shared_note=shared_note,
            key_prefix=key_prefix,
            default_data=default_data,
            default_meta=default_meta,
            actor=actor,
        )

    async def update_block_template(
        self,
        template_id: UUID,
        *,
        title: str | None = None,
        section: str | None = None,
        description: str | None = None,
        status: str | None = None,
        default_locale: str | None = None,
        available_locales: Collection[str] | None = None,
        block_type: str | None = None,
        category: str | None = None,
        sources: Collection[str] | None = None,
        surfaces: Collection[str] | None = None,
        owners: Collection[str] | None = None,
        catalog_locales: Collection[str] | None = None,
        documentation_url: str | None = None,
        keywords: Collection[str] | None = None,
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
        return await self._repo.update_block_template(
            template_id,
            title=title,
            section=section,
            description=description,
            status=status,
            default_locale=default_locale,
            available_locales=(
                list(available_locales) if available_locales is not None else None
            ),
            block_type=block_type,
            category=category,
            sources=list(sources) if sources is not None else None,
            surfaces=list(surfaces) if surfaces is not None else None,
            owners=list(owners) if owners is not None else None,
            catalog_locales=(
                list(catalog_locales) if catalog_locales is not None else None
            ),
            documentation_url=documentation_url,
            keywords=list(keywords) if keywords is not None else None,
            preview_kind=preview_kind,
            status_note=status_note,
            requires_publisher=requires_publisher,
            allow_shared_scope=allow_shared_scope,
            allow_page_scope=allow_page_scope,
            shared_note=shared_note,
            key_prefix=key_prefix,
            default_data=default_data,
            default_meta=default_meta,
            actor=actor,
        )

    async def create_global_block(
        self,
        *,
        key: str | None,
        title: str,
        section: str,
        locale: str | None,
        requires_publisher: bool,
        data: Mapping[str, Any] | None = None,
        meta: Mapping[str, Any] | None = None,
        actor: str | None = None,
        template_id: UUID | None = None,
        template_key: str | None = None,
    ) -> Block:
        return await self.create_block(
            key=key,
            title=title,
            template_id=template_id,
            template_key=template_key,
            section=section,
            scope=BlockScope.SHARED,
            default_locale=locale,
            requires_publisher=requires_publisher,
            data=data,
            meta=meta,
            actor=actor,
        )

    async def list_block_usage(
        self, block_id: UUID, *, section: str | None = None
    ) -> list[BlockUsage]:
        return await self._repo.list_block_usage(block_id, section=section)

    async def get_block_metrics(
        self,
        block_id: UUID,
        *,
        period: str = "7d",
        locale: str = "ru",
    ) -> BlockMetrics | None:
        return await self._repo.get_block_metrics(
            block_id,
            period=period,
            locale=locale,
        )

    async def get_global_block_metrics(
        self, block_id: UUID, *, period: str = "7d", locale: str = "ru"
    ) -> BlockMetrics | None:
        return await self.get_block_metrics(
            block_id,
            period=period,
            locale=locale,
        )

    async def list_block_history(
        self,
        block_id: UUID,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[BlockVersion], int]:
        return await self._repo.list_block_history(
            block_id,
            limit=limit,
            offset=offset,
        )

    async def list_global_block_history(
        self, block_id: UUID, *, limit: int = 10, offset: int = 0
    ) -> tuple[list[BlockVersion], int]:
        return await self.list_block_history(
            block_id,
            limit=limit,
            offset=offset,
        )

    async def get_block_version(
        self,
        block_id: UUID,
        version: int,
    ) -> BlockVersion:
        return await self._repo.get_block_version(block_id, version)

    async def get_global_block_version(
        self, block_id: UUID, version: int
    ) -> BlockVersion:
        return await self.get_block_version(block_id, version)

    async def restore_block_version(
        self,
        block_id: UUID,
        version: int,
        *,
        actor: str | None,
    ) -> Block:
        return await self._repo.restore_block_version(
            block_id,
            version,
            actor=actor,
        )

    async def restore_global_block_version(
        self, block_id: UUID, version: int, *, actor: str | None
    ) -> Block:
        return await self.restore_block_version(
            block_id,
            version,
            actor=actor,
        )

    async def list_audit(
        self,
        *,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        actor: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mapping[str, Any]], int]:
        return await self._repo.list_audit(
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            limit=limit,
            offset=offset,
        )

    async def _notify_block_publish(
        self,
        block: Block,
        usage: list[BlockUsage],
        *,
        audit_id: UUID,
        actor: str | None,
    ) -> None:
        if not self._notify_service:
            return
        owners: dict[str, list[BlockUsage]] = {}
        for item in usage:
            owner = (item.owner or "").strip() if item.owner else ""
            if not owner:
                continue
            owners.setdefault(owner, []).append(item)
        if not owners:
            return
        block_title = block.title or block.key
        for owner, entries in owners.items():
            pages_sorted = sorted(entries, key=lambda page: page.slug)
            summary_pages = pages_sorted[:5]
            page_list_text = ", ".join(page.slug for page in summary_pages)
            remaining = len(pages_sorted) - len(summary_pages)
            if remaining > 0:
                page_list_text += f" и ещё {remaining}"
            message = (
                f"Опубликована новая версия блока «{block_title}». "
                f"Затронутые страницы: {page_list_text}."
            )
            command = NotificationCreateCommand(
                user_id=owner,
                title=f"Блок «{block_title}» обновлён",
                message=message,
                type_="block_publish",
                placement="inbox",
                topic_key="site-editor.blocks",
                meta={
                    "block_id": str(block.id),
                    "block_key": block.key,
                    "block_title": block.title,
                    "pages": [
                        {
                            "page_id": str(page.page_id),
                            "slug": page.slug,
                            "title": page.title,
                            "status": page.status.value,
                            "section": page.section,
                        }
                        for page in pages_sorted
                    ],
                    "audit_id": str(audit_id),
                    "actor": actor,
                },
            )
            try:
                await self._notify_service.create_notification(command)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Failed to send global block publish notification",
                    exc_info=exc,
                    extra={"owner": owner, "block_id": str(block.id)},
                )

    async def _enqueue_page_republish_jobs(
        self, block_id: UUID, usage: list[BlockUsage]
    ) -> list[WorkerJob]:
        if not self._worker_queue:
            return []
        jobs: list[WorkerJob] = []
        seen: set[UUID] = set()
        for item in usage:
            page_id = item.page_id
            if page_id in seen:
                continue
            seen.add(page_id)
            command = JobCreateCommand(
                type="page_republish",
                input={
                    "page_id": str(page_id),
                    "block_id": str(block_id),
                    "reason": "block_publish",
                },
                priority=3,
                idempotency_key=f"page_republish:{page_id}:{block_id}",
            )
            job = await self._worker_queue.enqueue(command)
            jobs.append(job)
        return jobs


__all__ = ["SiteService"]
