from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.tag import Tag


async def get_or_create_tags(db: AsyncSession, slugs: Sequence[str]) -> list[Tag]:
    tags: list[Tag] = []
    for slug in slugs:
        result = await db.execute(select(Tag).where(Tag.slug == slug))
        tag = result.scalars().first()
        if not tag:
            tag = Tag(slug=slug, name=slug)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags
