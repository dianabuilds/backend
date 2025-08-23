from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Tag, ContentTag


class TagDAO:
    @staticmethod
    async def create(
        db: AsyncSession, *, slug: str, name: str, workspace_id: UUID
    ) -> Tag:
        tag = Tag(slug=slug, name=name, workspace_id=workspace_id)
        db.add(tag)
        await db.flush()
        return tag

    @staticmethod
    async def get_by_slug(
        db: AsyncSession, *, slug: str, workspace_id: UUID
    ) -> Tag | None:
        stmt = select(Tag).where(Tag.slug == slug, Tag.workspace_id == workspace_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession, *, q: Optional[str] = None, workspace_id: UUID
    ) -> List[Tag]:
        stmt = select(Tag).where(Tag.workspace_id == workspace_id)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
        stmt = stmt.order_by(Tag.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, tag: Tag) -> None:
        await db.delete(tag)
        await db.flush()

    @staticmethod
    async def usage_count(db: AsyncSession, tag_id: UUID, workspace_id: UUID) -> int:
        stmt = select(func.count(ContentTag.content_id)).where(
            ContentTag.tag_id == tag_id, ContentTag.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        return int(result.scalar() or 0)

    @staticmethod
    async def detach_all(db: AsyncSession, tag_id: UUID, workspace_id: UUID) -> None:
        stmt = delete(ContentTag).where(
            ContentTag.tag_id == tag_id, ContentTag.workspace_id == workspace_id
        )
        await db.execute(stmt)
        await db.flush()


class ContentTagDAO:
    @staticmethod
    async def attach(
        db: AsyncSession, *, content_id: UUID, tag_id: UUID, workspace_id: UUID
    ) -> ContentTag:
        item = ContentTag(
            content_id=content_id, tag_id=tag_id, workspace_id=workspace_id
        )
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def detach(
        db: AsyncSession, *, content_id: UUID, tag_id: UUID, workspace_id: UUID
    ) -> None:
        stmt = delete(ContentTag).where(
            ContentTag.content_id == content_id,
            ContentTag.tag_id == tag_id,
            ContentTag.workspace_id == workspace_id,
        )
        await db.execute(stmt)
        await db.flush()
