from __future__ import annotations

import builtins
import difflib
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload
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
        db: AsyncSession, *, node_type: str
    ) -> list[NodeItem]:
        stmt = select(NodeItem).options(selectinload(NodeItem.tags)).where(NodeItem.type == node_type)
        stmt = stmt.order_by(func.coalesce(NodeItem.published_at, func.now()).desc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        await NodePatchDAO.overlay(db, items)
        return items

    @staticmethod
    async def attach_tag(
        db: AsyncSession, *, node_id: int, tag_id: UUID
    ) -> ContentTag:
        item = ContentTag(content_id=node_id, tag_id=tag_id)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def detach_tag(
        db: AsyncSession, *, node_id: int, tag_id: UUID
    ) -> None:
        stmt = delete(ContentTag).where(
            ContentTag.content_id == node_id,
            ContentTag.tag_id == tag_id,
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def search(
        db: AsyncSession,
        *,
        node_type: str,
        q: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        stmt = select(NodeItem).options(selectinload(NodeItem.tags)).where(NodeItem.type == node_type)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(or_(NodeItem.title.ilike(pattern), NodeItem.summary.ilike(pattern)))
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
        node_id: int,
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
    async def revert(db: AsyncSession, *, patch_id: int) -> NodePatch | None:
        patch = await db.get(NodePatch, patch_id)
        if patch and patch.reverted_at is None:
            patch.reverted_at = datetime.utcnow()
            await db.flush()
        return patch

    @staticmethod
    async def get(db: AsyncSession, *, patch_id: int) -> NodePatch | None:
        return await db.get(NodePatch, patch_id)

    @staticmethod
    async def list(db: AsyncSession, *, node_id: int | None = None) -> list[NodePatch]:
        stmt = select(NodePatch)
        if node_id:
            stmt = stmt.where(NodePatch.node_id == node_id)
        stmt = stmt.order_by(NodePatch.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def diff(db: AsyncSession, patch: NodePatch) -> str:
        item = await db.get(NodeItem, patch.node_id)
        if not item:
            return ""
        mapper = inspect(NodeItem)
        original = {c.key: getattr(item, c.key) for c in mapper.column_attrs}
        patched = original.copy()
        if isinstance(patch.data, dict):
            patched.update(patch.data)
        original_json = json.dumps(original, sort_keys=True, indent=2, default=str)
        patched_json = json.dumps(patched, sort_keys=True, indent=2, default=str)
        diff = difflib.unified_diff(
            original_json.splitlines(),
            patched_json.splitlines(),
            fromfile="original",
            tofile="patched",
            lineterm="",
        )
        return "\n".join(diff)

    @staticmethod
    async def overlay(db: AsyncSession, items: builtins.list[NodeItem]) -> None:
        if not items:
            return
        ids = [i.id for i in items]
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
