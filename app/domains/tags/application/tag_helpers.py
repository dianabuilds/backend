from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.tags.infrastructure.models.tag_models import Tag


async def get_or_create_tags(db: AsyncSession, slugs: Sequence[str]) -> list[Tag]:
    res = await db.execute(select(Tag).where(Tag.slug.in_(list(slugs))))
    existing = {t.slug: t for t in res.scalars().all()}
    out: list[Tag] = []
    for slug in slugs:
        t = existing.get(slug)
        if not t:
            t = Tag(slug=slug, name=slug)
            db.add(t)
            await db.flush()
            existing[slug] = t
        out.append(t)
    return out
