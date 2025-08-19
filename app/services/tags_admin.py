from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, NodeTag
from app.models.tag_extras import TagAlias, TagMergeLog


def normalize_tag_name(name: str) -> str:
    return re.sub(r"\s+", " ", name or "").strip()


def normalize_alias(alias: str) -> str:
    return normalize_tag_name(alias).lower()


async def add_alias(db: AsyncSession, tag_id: UUID, alias: str, type_: str = "synonym") -> TagAlias:
    alias_norm = normalize_alias(alias)
    exists = (await db.execute(select(TagAlias).where(TagAlias.alias == alias_norm))).scalars().first()
    if exists:
        return exists
    item = TagAlias(tag_id=tag_id, alias=alias_norm, type=type_)
    db.add(item)
    await db.flush()
    return item


async def remove_alias(db: AsyncSession, alias_id: UUID) -> None:
    a = await db.get(TagAlias, alias_id)
    if a:
        await db.delete(a)


async def list_aliases(db: AsyncSession, tag_id: UUID) -> list[TagAlias]:
    res = await db.execute(select(TagAlias).where(TagAlias.tag_id == tag_id).order_by(TagAlias.alias.asc()))
    return list(res.scalars().all())


async def dry_run_merge(db: AsyncSession, from_id: UUID, to_id: UUID) -> Dict[str, Any]:
    if str(from_id) == str(to_id):
        return {"errors": ["from and to tags must be different"]}
    from_tag = await db.get(Tag, from_id)
    to_tag = await db.get(Tag, to_id)
    if not from_tag or not to_tag:
        return {"errors": ["tag not found"]}
    # Сколько связей будет затронуто
    cnt = (await db.execute(select(func.count(NodeTag.node_id)).where(NodeTag.tag_id == from_id))).scalar() or 0
    # Сколько алиасов переедет
    aliases = (await db.execute(select(func.count(TagAlias.id)).where(TagAlias.tag_id == from_id))).scalar() or 0
    return {
        "from": {"id": str(from_tag.id), "name": from_tag.name, "slug": from_tag.slug},
        "to": {"id": str(to_tag.id), "name": to_tag.name, "slug": to_tag.slug},
        "content_touched": int(cnt),
        "aliases_moved": int(aliases),
        "warnings": [],
        "errors": [],
    }


async def apply_merge(db: AsyncSession, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None) -> Dict[str, Any]:
    report = await dry_run_merge(db, from_id, to_id)
    if report.get("errors"):
        return report
    # Перевешиваем связи NodeTag
    await db.execute(
        update(NodeTag)
        .where(NodeTag.tag_id == from_id)
        .values(tag_id=to_id)
    )
    # Перенос алиасов
    res = await db.execute(select(TagAlias).where(TagAlias.tag_id == from_id))
    for a in res.scalars().all():
        a.tag_id = to_id
    # Удаляем исходный тег
    from_tag = await db.get(Tag, from_id)
    if from_tag:
        await db.delete(from_tag)
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
    db.add(log)
    await db.flush()
    return report
