from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ContentItem, ContentPatch
from app.domains.tags.models import ContentTag
from datetime import datetime
from sqlalchemy.orm.attributes import set_committed_value


class ContentItemDAO:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> ContentItem:
        item = ContentItem(**kwargs)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def list_by_type(
        db: AsyncSession, *, workspace_id: UUID, content_type: str
    ) -> List[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(
                ContentItem.workspace_id == workspace_id,
                ContentItem.type == content_type,
            )
            .order_by(func.coalesce(ContentItem.published_at, func.now()).desc())
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        await ContentPatchDAO.overlay(db, items)
        return items

    @staticmethod
    async def attach_tag(
        db: AsyncSession, *, content_id: UUID, tag_id: UUID, workspace_id: UUID
    ) -> ContentTag:
        item = ContentTag(
            content_id=content_id, tag_id=tag_id, workspace_id=workspace_id
        )
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def detach_tag(db: AsyncSession, *, content_id: UUID, tag_id: UUID) -> None:
        stmt = delete(ContentTag).where(
            ContentTag.content_id == content_id, ContentTag.tag_id == tag_id
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def search(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        content_type: str,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[ContentItem]:
        stmt = select(ContentItem).where(
            ContentItem.workspace_id == workspace_id,
            ContentItem.type == content_type,
        )
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(ContentItem.title.ilike(pattern), ContentItem.summary.ilike(pattern))
            )
        stmt = stmt.order_by(func.coalesce(ContentItem.published_at, func.now()).desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        await ContentPatchDAO.overlay(db, items)
        return items


class ContentPatchDAO:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        content_id: UUID,
        data: dict,
        created_by_user_id: UUID | None = None,
    ) -> ContentPatch:
        patch = ContentPatch(
            content_id=content_id,
            data=data,
            created_by_user_id=created_by_user_id,
        )
        db.add(patch)
        await db.flush()
        return patch

    @staticmethod
    async def revert(db: AsyncSession, *, patch_id: UUID) -> ContentPatch | None:
        patch = await db.get(ContentPatch, patch_id)
        if patch and patch.reverted_at is None:
            patch.reverted_at = datetime.utcnow()
            await db.flush()
        return patch

    @staticmethod
    async def overlay(db: AsyncSession, items: list[ContentItem]) -> None:
        if not items:
            return
        ids = [i.id for i in items]
        for item in items:
            await db.refresh(item)
        stmt = select(ContentPatch).where(
            ContentPatch.content_id.in_(ids),
            ContentPatch.reverted_at.is_(None),
        )
        res = await db.execute(stmt)
        patches = {p.content_id: p for p in res.scalars().all()}
        for item in items:
            patch = patches.get(item.id)
            if patch:
                for key, value in patch.data.items():
                    if hasattr(item, key):
                        set_committed_value(item, key, value)
