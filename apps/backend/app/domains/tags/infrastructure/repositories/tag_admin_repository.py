from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tags.application.ports.tag_admin_port import ITagAdminRepository
from app.domains.tags.infrastructure.models.tag_models import (
    NodeTag,
    TagAlias,
    TagMergeLog,
)
from app.domains.tags.models import Tag


class TagAdminRepository(ITagAdminRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_alias(
        self, tag_id: UUID, alias_norm: str, type_: str = "synonym"
    ) -> TagAlias:
        exists = (
            (
                await self._db.execute(
                    select(TagAlias).where(TagAlias.alias == alias_norm)
                )
            )
            .scalars()
            .first()
        )
        if exists:
            return exists
        item = TagAlias(tag_id=tag_id, alias=alias_norm, type=type_)
        self._db.add(item)
        await self._db.flush()
        return item

    async def remove_alias(self, alias_id: UUID) -> None:
        a = await self._db.get(TagAlias, alias_id)
        if a:
            await self._db.delete(a)

    async def list_aliases(self, tag_id: UUID) -> list[TagAlias]:
        res = await self._db.execute(
            select(TagAlias)
            .where(TagAlias.tag_id == tag_id)
            .order_by(TagAlias.alias.asc())
        )
        return list(res.scalars().all())

    async def dry_run_merge(self, from_id: UUID, to_id: UUID) -> dict[str, Any]:
        if str(from_id) == str(to_id):
            return {"errors": ["from and to tags must be different"]}
        from_tag = await self._db.get(Tag, from_id)
        to_tag = await self._db.get(Tag, to_id)
        if not from_tag or not to_tag:
            return {"errors": ["tag not found"]}
        cnt = (
            await self._db.execute(
                select(func.count(NodeTag.node_id)).where(NodeTag.tag_id == from_id)
            )
        ).scalar() or 0
        aliases = (
            await self._db.execute(
                select(func.count(TagAlias.id)).where(TagAlias.tag_id == from_id)
            )
        ).scalar() or 0
        return {
            "from": {
                "id": str(from_tag.id),
                "name": from_tag.name,
                "slug": from_tag.slug,
            },
            "to": {"id": str(to_tag.id), "name": to_tag.name, "slug": to_tag.slug},
            "content_touched": int(cnt),
            "aliases_moved": int(aliases),
            "warnings": [],
            "errors": [],
        }

    async def apply_merge(
        self, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None
    ) -> dict[str, Any]:
        report = await self.dry_run_merge(from_id, to_id)
        if report.get("errors"):
            return report
        # Перевешиваем связи NodeTag
        await self._db.execute(
            update(NodeTag).where(NodeTag.tag_id == from_id).values(tag_id=to_id)
        )
        # Перенос алиасов
        res = await self._db.execute(select(TagAlias).where(TagAlias.tag_id == from_id))
        for a in res.scalars().all():
            a.tag_id = to_id
        # Удаляем исходный тег
        from_tag = await self._db.get(Tag, from_id)
        if from_tag:
            await self._db.delete(from_tag)
        # Лог
        log = TagMergeLog(
            from_tag_id=from_id,
            to_tag_id=to_id,
            merged_by=actor_id,
            merged_at=datetime.utcnow(),
            dry_run=False,
            reason=reason or None,
            report=report,
        )
        self._db.add(log)
        await self._db.flush()
        return report
