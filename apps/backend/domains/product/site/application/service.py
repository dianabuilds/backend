from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any
from uuid import UUID

from domains.platform.worker.application.service import (
    JobCreateCommand,
    WorkerQueueService,
)
from domains.platform.worker.domain.models import WorkerJob
from domains.product.site.domain import (
    GlobalBlock,
    GlobalBlockMetrics,
    GlobalBlockStatus,
    GlobalBlockUsage,
    GlobalBlockVersion,
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


class SiteService:
    """Application facade for site editor use cases."""

    def __init__(
        self,
        repository: SiteRepository,
        validator: PageDraftValidator | None = None,
        worker_queue: WorkerQueueService | None = None,
    ) -> None:
        self._repo = repository
        self._validator = validator or PageDraftValidator()
        self._worker_queue = worker_queue

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
                "site.admin",
                "site.publisher",
                "site.editor",
                "site.reviewer",
                "admin",
                "moderator",
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
    ) -> Page:
        return await self._repo.create_page(
            slug=slug,
            page_type=page_type,
            title=title,
            locale=locale,
            owner=owner,
            actor=actor,
        )

    async def get_page(self, page_id: UUID) -> Page:
        return await self._repo.get_page(page_id)

    async def get_page_draft(self, page_id: UUID) -> PageDraft:
        return await self._repo.get_page_draft(page_id)

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
        return await self._repo.publish_page(
            page_id=page_id,
            actor=actor,
            comment=comment,
            diff=diff,
        )

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
        return await self._repo.list_global_blocks(
            page=page,
            page_size=page_size,
            section=section,
            status=status,
            locale=locale,
            query=query,
            has_draft=has_draft,
            sort=sort,
        )

    async def get_global_block(self, block_id: UUID) -> GlobalBlock:
        return await self._repo.get_global_block(block_id)

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
        return await self._repo.save_global_block(
            block_id=block_id,
            payload=payload,
            meta=meta,
            version=version,
            comment=comment,
            review_status=review_status,
            actor=actor,
        )

    async def publish_global_block(
        self,
        *,
        block_id: UUID,
        actor: str | None,
        comment: str | None,
        diff: list[Mapping[str, Any]] | None = None,
    ) -> tuple[GlobalBlock, UUID, list[GlobalBlockUsage], list[WorkerJob]]:
        block, audit_id = await self._repo.publish_global_block(
            block_id=block_id,
            actor=actor,
            comment=comment,
            diff=diff,
        )
        await self._repo.refresh_global_block_usage_count(block_id)
        usage = await self._repo.list_block_usage(block_id)
        jobs = await self._enqueue_page_republish_jobs(block_id, usage)
        refreshed_block = await self._repo.get_global_block(block_id)
        return refreshed_block, audit_id, usage, jobs

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
        return await self._repo.create_global_block(
            key=key,
            title=title,
            section=section,
            locale=locale,
            requires_publisher=requires_publisher,
            data=data,
            meta=meta,
            actor=actor,
        )

    async def list_block_usage(
        self, block_id: UUID, *, section: str | None = None
    ) -> list[GlobalBlockUsage]:
        return await self._repo.list_block_usage(block_id, section=section)

    async def get_global_block_metrics(
        self, block_id: UUID, *, period: str = "7d", locale: str = "ru"
    ) -> GlobalBlockMetrics | None:
        return await self._repo.get_global_block_metrics(block_id, period=period, locale=locale)

    async def list_global_block_history(
        self, block_id: UUID, *, limit: int = 10, offset: int = 0
    ) -> tuple[list[GlobalBlockVersion], int]:
        return await self._repo.list_global_block_history(block_id, limit=limit, offset=offset)

    async def get_global_block_version(self, block_id: UUID, version: int) -> GlobalBlockVersion:
        return await self._repo.get_global_block_version(block_id, version)

    async def restore_global_block_version(
        self, block_id: UUID, version: int, *, actor: str | None
    ) -> GlobalBlock:
        return await self._repo.restore_global_block_version(block_id, version, actor=actor)

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

    async def _enqueue_page_republish_jobs(
        self, block_id: UUID, usage: list[GlobalBlockUsage]
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
                    "reason": "global_block_publish",
                },
                priority=3,
                idempotency_key=f"page_republish:{page_id}:{block_id}",
            )
            job = await self._worker_queue.enqueue(command)
            jobs.append(job)
        return jobs


__all__ = ["SiteService"]
