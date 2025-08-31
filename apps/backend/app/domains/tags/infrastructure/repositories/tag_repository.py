from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tags.application.ports.tag_repo_port import ITagRepository
from app.domains.tags.infrastructure.models.tag_models import (
    NodeTag,
    TagAlias,
    TagBlacklist,
    TagMergeLog,
)
from app.domains.tags.models import Tag


class TagRepository(ITagRepository):
    """
    Минимальный репозиторий для совместимости со старыми местами использования.
    Реализует только get_by_slug/create.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_slug(self, slug: str) -> Tag | None:
        res = await self._db.execute(select(Tag).where(Tag.slug == slug))
        return res.scalars().first()

    async def create(self, slug: str, name: str) -> Tag:
        tag = Tag(slug=slug, name=name)
        self._db.add(tag)
        await self._db.flush()
        return tag

    # Остальные методы протокола здесь не используются
    async def list_with_counters(
        self, q: str | None, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def list_aliases(self, tag_id: UUID) -> list[TagAlias]:
        raise NotImplementedError

    async def add_alias(self, tag_id: UUID, alias: str) -> TagAlias:
        raise NotImplementedError

    async def remove_alias(self, alias_id: UUID) -> None:
        raise NotImplementedError

    async def blacklist_list(self, q: str | None) -> list[TagBlacklist]:
        raise NotImplementedError

    async def blacklist_add(self, slug: str, reason: str | None) -> TagBlacklist:
        raise NotImplementedError

    async def blacklist_delete(self, slug: str) -> None:
        raise NotImplementedError

    async def create_tag(self, slug: str, name: str) -> Tag:
        raise NotImplementedError

    async def delete_tag(self, tag_id: UUID) -> None:
        raise NotImplementedError

    async def merge_dry_run(self, from_id: UUID, to_id: UUID) -> dict[str, Any]:
        raise NotImplementedError

    async def merge_apply(
        self, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None
    ) -> dict[str, Any]:
        raise NotImplementedError


class TagRepositoryAdapter(ITagRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # Listing
    async def list_with_counters(
        self, q: str | None, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                Tag,
                func.count(func.distinct(NodeTag.node_id)).label("usage_count"),
                func.count(func.distinct(TagAlias.id)).label("aliases_count"),
            )
            .join(NodeTag, Tag.id == NodeTag.tag_id, isouter=True)
            .join(TagAlias, Tag.id == TagAlias.tag_id, isouter=True)
            .group_by(Tag.id)
        )
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
        stmt = stmt.order_by(desc("usage_count"), Tag.name).offset(offset).limit(limit)
        res = await self._db.execute(stmt)
        rows = res.all()
        out: list[dict[str, Any]] = []
        for tag, usage, aliases in rows:
            out.append(
                {
                    "id": tag.id,
                    "slug": tag.slug,
                    "name": tag.name,
                    "created_at": tag.created_at,
                    "usage_count": int(usage or 0),
                    "aliases_count": int(aliases or 0),
                    "is_hidden": bool(tag.is_hidden),
                }
            )
        return out

    # Aliases
    async def list_aliases(self, tag_id: UUID) -> list[TagAlias]:
        res = await self._db.execute(
            select(TagAlias)
            .where(TagAlias.tag_id == tag_id)
            .order_by(TagAlias.alias.asc())
        )
        return list(res.scalars().all())

    async def add_alias(self, tag_id: UUID, alias: str) -> TagAlias:
        existing = await self._db.execute(
            select(TagAlias).where(TagAlias.tag_id == tag_id, TagAlias.alias == alias)
        )
        found = existing.scalars().first()
        if found:
            return found
        item = TagAlias(tag_id=tag_id, alias=alias)
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def remove_alias(self, alias_id: UUID) -> None:
        res = await self._db.get(TagAlias, alias_id)
        if res:
            await self._db.delete(res)
            await self._db.flush()

    # Blacklist
    async def blacklist_list(self, q: str | None) -> list[TagBlacklist]:
        stmt = select(TagBlacklist)
        if q:
            stmt = stmt.where(TagBlacklist.slug.ilike(f"%{q}%"))
        stmt = stmt.order_by(TagBlacklist.created_at.desc())
        return list((await self._db.execute(stmt)).scalars().all())

    async def blacklist_add(self, slug: str, reason: str | None) -> TagBlacklist:
        existing = await self._db.get(TagBlacklist, slug)
        if existing:
            return existing
        item = TagBlacklist(slug=slug, reason=reason)
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def blacklist_delete(self, slug: str) -> None:
        item = await self._db.get(TagBlacklist, slug)
        if item:
            await self._db.delete(item)
            await self._db.flush()

    # CRUD
    async def create_tag(self, slug: str, name: str) -> Tag:
        # Проверка blacklist
        in_blacklist = await self._db.get(TagBlacklist, slug)
        if in_blacklist:
            raise ValueError("Slug is blacklisted")
        # Дубликаты
        existing = await self._db.execute(select(Tag).where(Tag.slug == slug))
        if existing.scalar_one_or_none():
            raise ValueError("Tag already exists")
        tag = Tag(slug=slug, name=name)
        self._db.add(tag)
        await self._db.flush()
        await self._db.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: UUID) -> None:
        await self._db.execute(delete(TagAlias).where(TagAlias.tag_id == tag_id))
        await self._db.execute(delete(NodeTag).where(NodeTag.tag_id == tag_id))
        tag = await self._db.get(Tag, tag_id)
        if tag:
            await self._db.delete(tag)
        await self._db.flush()

    # Merge
    async def merge_dry_run(self, from_id: UUID, to_id: UUID) -> dict[str, Any]:
        if str(from_id) == str(to_id):
            return {"errors": ["from and to tags must be different"], "warnings": []}
        from_tag = await self._db.get(Tag, from_id)
        to_tag = await self._db.get(Tag, to_id)
        if not from_tag or not to_tag:
            return {"errors": ["tag not found"], "warnings": []}
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

    async def merge_apply(
        self, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None
    ) -> dict[str, Any]:
        # Валидируем и формируем отчёт
        report = await self.merge_dry_run(from_id, to_id)
        if report.get("errors"):
            return report

        # Удаляем потенциальные дубликаты NodeTag(to_id) для тех же node_id, что привязаны к from_id
        subq = (
            select(NodeTag.node_id).where(NodeTag.tag_id == from_id).scalar_subquery()
        )
        await self._db.execute(
            delete(NodeTag).where(NodeTag.tag_id == to_id, NodeTag.node_id.in_(subq))
        )

        # Перевешиваем связи NodeTag
        await self._db.execute(
            update(NodeTag).where(NodeTag.tag_id == from_id).values(tag_id=to_id)
        )

        # Переносим алиасы на целевой тег
        res = await self._db.execute(select(TagAlias).where(TagAlias.tag_id == from_id))
        for alias in res.scalars().all():
            alias.tag_id = to_id

        # Удаляем исходный тег
        from_tag = await self._db.get(Tag, from_id)
        if from_tag:
            await self._db.delete(from_tag)

        # Лог слияния
        self._db.add(
            TagMergeLog(
                from_tag_id=from_id,
                to_tag_id=to_id,
                merged_by=actor_id,
                merged_at=datetime.utcnow(),
                dry_run=False,
                reason=reason or None,
                report=report,
            )
        )
        await self._db.flush()
        return report

    # Совместимость
    async def get_by_slug(self, slug: str) -> Tag | None:
        res = await self._db.execute(select(Tag).where(Tag.slug == slug))
        return res.scalars().first()

    async def create(self, slug: str, name: str) -> Tag:
        tag = Tag(slug=slug, name=name)
        self._db.add(tag)
        await self._db.flush()
        return tag
