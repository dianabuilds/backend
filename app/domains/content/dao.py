from __future__ import annotations

from typing import List, Optional

from sqlalchemy import or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ContentItem


class ContentItemDAO:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> ContentItem:
        item = ContentItem(**kwargs)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def list_by_type(db: AsyncSession, content_type: str) -> List[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.type == content_type)
            .order_by(func.coalesce(ContentItem.published_at, func.now()).desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def search(
        db: AsyncSession,
        *,
        content_type: str,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[ContentItem]:
        stmt = select(ContentItem).where(ContentItem.type == content_type)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(ContentItem.title.ilike(pattern), ContentItem.summary.ilike(pattern))
            )
        stmt = stmt.order_by(func.coalesce(ContentItem.published_at, func.now()).desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        return list(result.scalars().all())
