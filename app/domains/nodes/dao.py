from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.domains.tags.models import ContentTag

from .models import NodeItem, NodePatch


class NodeItemDAO:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> NodeItem:
        item = NodeItem(**kwargs)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def list_by_type(
        db: AsyncSession, *, workspace_id: UUID, node_type: str
    ) -> list[NodeItem]:
        stmt = (
            select(NodeItem)
            .where(
                NodeItem.workspace_id == workspace_id,
                NodeItem.type == node_type,
            )
            .order_by(func.coalesce(NodeItem.published_at, func.now()).desc())
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        await NodePatchDAO.overlay(db, items)
        return items

    @staticmethod
    async def attach_tag(
        db: AsyncSession, *, node_id: UUID, tag_id: UUID, workspace_id: UUID
    ) -> ContentTag:
        item = ContentTag(content_id=node_id, tag_id=tag_id, workspace_id=workspace_id)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def detach_tag(db: AsyncSession, *, node_id: UUID, tag_id: UUID) -> None:
        stmt = delete(ContentTag).where(
            ContentTag.content_id == node_id, ContentTag.tag_id == tag_id
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def search(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        node_type: str,
        q: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        stmt = select(NodeItem).where(
            NodeItem.workspace_id == workspace_id,
            NodeItem.type == node_type,
        )
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(NodeItem.title.ilike(pattern), NodeItem.summary.ilike(pattern))
            )
        stmt = stmt.order_by(func.coalesce(NodeItem.published_at, func.now()).desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        await NodePatchDAO.overlay(db, items)
        return items


class NodePatchDAO:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        node_id: UUID,
        data: dict,
        created_by_user_id: UUID | None = None,
    ) -> NodePatch:
        patch = NodePatch(
            node_id=node_id,
            data=data,
            created_by_user_id=created_by_user_id,
        )
        db.add(patch)
        await db.flush()
        return patch

    @staticmethod
    async def revert(db: AsyncSession, *, patch_id: UUID) -> NodePatch | None:
        patch = await db.get(NodePatch, patch_id)
        if patch and patch.reverted_at is None:
            patch.reverted_at = datetime.utcnow()
            await db.flush()
        return patch

    @staticmethod
    async def overlay(db: AsyncSession, items: list[NodeItem]) -> None:
        if not items:
            return
        ids = [i.id for i in items]
        for item in items:
            await db.refresh(item)
        stmt = select(NodePatch).where(
            NodePatch.node_id.in_(ids),
            NodePatch.reverted_at.is_(None),
        )
        res = await db.execute(stmt)
        patches = {p.node_id: p for p in res.scalars().all()}
        for item in items:
            patch = patches.get(item.id)
            if patch:
                for key, value in patch.data.items():
                    if hasattr(item, key):
                        set_committed_value(item, key, value)
