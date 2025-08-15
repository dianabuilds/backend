from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.tag import Tag


class TagRepository:
    """Persistence helper for tags."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, slug: str) -> Tag:
        result = await self.session.execute(select(Tag).where(Tag.slug == slug))
        tag = result.scalars().first()
        if not tag:
            tag = Tag(slug=slug, name=slug)
            self.session.add(tag)
            await self.session.flush()
        return tag

    async def get_or_create_many(self, slugs: Sequence[str]) -> list[Tag]:
        tags: list[Tag] = []
        for slug in slugs:
            tags.append(await self.get_or_create(slug))
        return tags
