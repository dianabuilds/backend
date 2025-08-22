from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.infrastructure.models.tag_models import Tag, NodeTag
from app.repositories import NodeRepository as _LegacyNodeRepository
from app.schemas.node import NodeCreate, NodeUpdate


class NodeRepositoryAdapter(INodeRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = _LegacyNodeRepository(db)

    async def get_by_slug(self, slug: str) -> Node | None:
        return await self._repo.get_by_slug(slug)

    async def get_by_id(self, node_id: UUID) -> Node | None:
        return await self._repo.get_by_id(node_id)

    async def create(self, payload: NodeCreate, author_id: UUID) -> Node:
        return await self._repo.create(payload, author_id)

    async def update(self, node: Node, payload: NodeUpdate) -> Node:
        return await self._repo.update(node, payload)

    async def delete(self, node: Node) -> None:
        await self._repo.delete(node)

    async def set_tags(self, node: Node, tags: list[str]) -> Node:
        return await self._repo.set_tags(node, tags)

    async def increment_views(self, node: Node) -> Node:
        return await self._repo.increment_views(node)

    async def update_reactions(self, node: Node, reaction: str, action: str) -> Node:
        return await self._repo.update_reactions(node, reaction, action)

    async def list_by_author(self, author_id: UUID, limit: int = 50, offset: int = 0) -> List[Node]:
        res = await self._db.execute(
            select(Node).where(Node.author_id == author_id).order_by(Node.created_at.desc()).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def bulk_set_visibility(self, node_ids: List[UUID], is_visible: bool) -> int:
        if not node_ids:
            return 0
        count = 0
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n is None:
                continue
            n.is_visible = bool(is_visible)
            count += 1
        await self._db.flush()
        return count

    async def bulk_set_public(self, node_ids: List[UUID], is_public: bool) -> int:
        if not node_ids:
            return 0
        count = 0
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n is None:
                continue
            n.is_public = bool(is_public)
            count += 1
        await self._db.flush()
        return count

    async def bulk_set_tags(self, node_ids: List[UUID], tags: list[str]) -> int:
        from app.domains.tags.infrastructure.models.tag_models import Tag, NodeTag
        if not node_ids:
            return 0
        # Ensure tags exist
        tag_ids: list[UUID] = []
        for slug in tags:
            slug_norm = (slug or "").strip().lower()
            if not slug_norm:
                continue
            existing = await self._db.execute(select(Tag).where(Tag.slug == slug_norm))
            tag = existing.scalar_one_or_none()
            if not tag:
                tag = Tag(slug=slug_norm, name=slug_norm)
                self._db.add(tag)
                await self._db.flush()
                await self._db.refresh(tag)
            tag_ids.append(tag.id)
        # Replace relations for provided nodes
        await self._db.execute(delete(NodeTag).where(NodeTag.node_id.in_(node_ids)))
        for nid in node_ids:
            for tid in tag_ids:
                self._db.add(NodeTag(node_id=nid, tag_id=tid))
        await self._db.flush()
        return len(node_ids)

    async def bulk_set_tags_diff(self, node_ids: List[UUID], add: list[str], remove: list[str]) -> int:
        from app.domains.tags.infrastructure.models.tag_models import Tag, NodeTag
        if not node_ids:
            return 0
        add_ids: list[UUID] = []
        for slug in add:
            slug_norm = (slug or "").strip().lower()
            if not slug_norm:
                continue
            existing = await self._db.execute(select(Tag).where(Tag.slug == slug_norm))
            tag = existing.scalar_one_or_none()
            if not tag:
                tag = Tag(slug=slug_norm, name=slug_norm)
                self._db.add(tag)
                await self._db.flush()
                await self._db.refresh(tag)
            add_ids.append(tag.id)
        # Remove relations
        if remove:
            rem_q = await self._db.execute(select(Tag.id).where(Tag.slug.in_([s.strip().lower() for s in remove])))
            rem_ids = [row[0] for row in rem_q.all()]
            if rem_ids:
                await self._db.execute(delete(NodeTag).where(NodeTag.node_id.in_(node_ids), NodeTag.tag_id.in_(rem_ids)))
        # Add new relations
        for nid in node_ids:
            for tid in add_ids:
                self._db.add(NodeTag(node_id=nid, tag_id=tid))
        await self._db.flush()
        return len(node_ids)
