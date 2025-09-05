from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tags.application.ports.tag_repo_port import ITagRepository
from app.domains.telemetry.application.audit_service import AuditService
from app.domains.telemetry.infrastructure.repositories.audit_repository import (
    AuditLogRepository,
)


async def _audit(
    db: AsyncSession,
    *,
    actor_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    reason: str | None = None,
    request=None,
) -> None:
    """
    Внутренний хелпер: вызов доменного сервиса аудита с извлечением
     IP/User-Agent из request (если есть).
    """
    ip = None
    ua = None
    try:
        if request is not None and hasattr(request, "headers"):
            ip = request.headers.get("x-forwarded-for") or getattr(
                getattr(request, "client", None), "host", None
            )
            ua = request.headers.get("user-agent")
    except Exception:
        pass
    service = AuditService(AuditLogRepository(db))
    await service.log(
        actor_id=actor_id or "",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        ip=ip,
        user_agent=ua,
        reason=reason,
        extra=None,
    )


class TagAdminService:
    def __init__(self, repo: ITagRepository) -> None:
        self._repo = repo

    # Helpers
    @staticmethod
    def normalize_tag_name(name: str) -> str:
        return re.sub(r"\s+", " ", name or "").strip()

    @staticmethod
    def normalize_alias(alias: str) -> str:
        return TagAdminService.normalize_tag_name(alias).lower()

    # Queries
    async def list_tags(self, q: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        return await self._repo.list_with_counters(q, limit, offset)

    async def list_aliases(self, tag_id: UUID):
        return await self._repo.list_aliases(tag_id)

    # Mutations with audit
    async def add_alias(
        self,
        db: AsyncSession,
        tag_id: UUID,
        alias: str,
        actor_id: str | None,
        request=None,
    ):
        alias_norm = self.normalize_alias(alias)
        item = await self._repo.add_alias(tag_id, alias_norm)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_alias_add",
                resource_type="tag",
                resource_id=str(tag_id),
                after={"alias": item.alias},
                request=request,
            )
        except Exception:
            pass
        return item

    async def remove_alias(
        self,
        db: AsyncSession,
        alias_id: UUID,
        actor_id: str | None,
        tag_id: str | None,
        request=None,
    ):
        await self._repo.remove_alias(alias_id)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_alias_remove",
                resource_type="tag",
                resource_id=str(tag_id) if tag_id else "",
                before={"alias_id": str(alias_id)},
                request=request,
            )
        except Exception:
            pass

    async def blacklist_list(self, q: str | None):
        return await self._repo.blacklist_list(q)

    async def blacklist_add(
        self,
        db: AsyncSession,
        slug: str,
        reason: str | None,
        actor_id: str | None,
        request=None,
    ):
        item = await self._repo.blacklist_add(slug, reason)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_blacklist_add",
                resource_type="tag_blacklist",
                resource_id=slug,
                after={"slug": slug, "reason": reason},
                request=request,
            )
        except Exception:
            pass
        return item

    async def blacklist_delete(
        self, db: AsyncSession, slug: str, actor_id: str | None, request=None
    ):
        await self._repo.blacklist_delete(slug)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_blacklist_remove",
                resource_type="tag_blacklist",
                resource_id=slug,
                before={"slug": slug},
                request=request,
            )
        except Exception:
            pass

    async def create_tag(
        self, db: AsyncSession, slug: str, name: str, actor_id: str | None, request=None
    ):
        tag = await self._repo.create_tag(slug, name)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_create",
                resource_type="tag",
                resource_id=str(tag.id),
                after={"id": str(tag.id), "slug": tag.slug, "name": tag.name},
                request=request,
            )
        except Exception:
            pass
        return tag

    async def delete_tag(self, db: AsyncSession, tag_id: UUID, actor_id: str | None, request=None):
        await self._repo.delete_tag(tag_id)
        try:
            await _audit(
                db,
                actor_id=actor_id,
                action="tag_delete",
                resource_type="tag",
                resource_id=str(tag_id),
                before={"id": str(tag_id)},
                request=request,
            )
        except Exception:
            pass

    # Merge
    async def dry_run_merge(self, from_id: UUID, to_id: UUID) -> dict[str, Any]:
        return await self._repo.merge_dry_run(from_id, to_id)

    async def apply_merge(
        self,
        db: AsyncSession,
        from_id: UUID,
        to_id: UUID,
        actor_id: str | None,
        reason: str | None,
        request=None,
    ) -> dict[str, Any]:
        report = await self._repo.merge_apply(from_id, to_id, actor_id, reason)
        if not report.get("errors"):
            try:
                await _audit(
                    db,
                    actor_id=actor_id,
                    action="tag_merge_apply",
                    resource_type="tag",
                    resource_id=f"{from_id}->{to_id}",
                    after=report,
                    request=request,
                    reason=reason or None,
                )
            except Exception:
                pass
        return report
