from __future__ import annotations

"""Concrete implementation of :class:`INodeRepository`.

The original project relied on a legacy repository located in
``app.repositories``.  In this kata the legacy module is absent which caused
import errors and, as a consequence, any router depending on the repository was
silently skipped.  The admin and public node APIs therefore responded with 404.

This adapter re‑implements the small subset of functionality needed by the
current tests using plain SQLAlchemy queries.  If the legacy repository becomes
available the adapter will delegate to it automatically.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.schemas.node import NodeCreate, NodeUpdate

try:  # pragma: no cover - optional legacy dependency
    from app.repositories import NodeRepository as _LegacyNodeRepository  # type: ignore
except Exception:  # pragma: no cover
    _LegacyNodeRepository = None


class NodeRepositoryAdapter(INodeRepository):
    """Repository used by API endpoints.

    The implementation delegates to ``_LegacyNodeRepository`` when it is
    available; otherwise a lightweight SQLAlchemy based version is used.  Only
    methods required by the tests/admin pages are implemented.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = _LegacyNodeRepository(db) if _LegacyNodeRepository else None

    # ------------------------------------------------------------------
    # Basic getters
    async def get_by_slug(self, slug: str, workspace_id: UUID) -> Node | None:
        if self._repo:
            return await self._repo.get_by_slug(slug, workspace_id=workspace_id)
        res = await self._db.execute(
            select(Node).where(Node.slug == slug, Node.workspace_id == workspace_id)
        )
        return res.scalar_one_or_none()

    async def get_by_id(self, node_id: UUID, workspace_id: UUID) -> Node | None:
        if self._repo:
            return await self._repo.get_by_id(node_id, workspace_id=workspace_id)
        res = await self._db.execute(
            select(Node).where(Node.id == node_id, Node.workspace_id == workspace_id)
        )
        return res.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Mutating operations
    async def create(self, payload: NodeCreate, author_id: UUID, workspace_id: UUID) -> Node:
        if self._repo:
            return await self._repo.create(payload, author_id, workspace_id)
        node = Node(
            title=payload.title,
            content=payload.content,
            media=payload.media or [],
            cover_url=payload.cover_url,
            author_id=author_id,
            workspace_id=workspace_id,
            is_public=payload.is_public,
            is_visible=payload.is_visible,
            meta=payload.meta or {},
            premium_only=payload.premium_only or False,
            nft_required=payload.nft_required,
            ai_generated=payload.ai_generated or False,
            allow_feedback=payload.allow_feedback,
            is_recommendable=payload.is_recommendable,
            created_by_user_id=author_id,
        )
        self._db.add(node)
        await self._db.flush()
        if payload.tags:
            await self.set_tags(node, payload.tags, author_id)
        await self._db.commit()
        await self._db.refresh(node)
        return node

    async def update(self, node: Node, payload: NodeUpdate, actor_id: UUID) -> Node:
        if self._repo:
            return await self._repo.update(node, payload, actor_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "tags" or value is None:
                continue
            setattr(node, field, value)
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = actor_id
        if payload.tags is not None:
            await self.set_tags(node, payload.tags, actor_id)
        await self._db.commit()
        await self._db.refresh(node)
        return node

    async def delete(self, node: Node) -> None:
        if self._repo:
            await self._repo.delete(node)
            return
        await self._db.delete(node)
        await self._db.commit()

    async def set_tags(self, node: Node, tags: list[str], actor_id: UUID) -> Node:
        if self._repo:
            return await self._repo.set_tags(node, tags, actor_id)
        from app.domains.tags.models import Tag
        tag_ids: list[UUID] = []
        for slug in tags:
            slug_norm = (slug or "").strip().lower()
            if not slug_norm:
                continue
            res = await self._db.execute(select(Tag).where(Tag.slug == slug_norm))
            tag = res.scalar_one_or_none()
            if not tag:
                tag = Tag(slug=slug_norm, name=slug_norm)
                self._db.add(tag)
                await self._db.flush()
                await self._db.refresh(tag)
            tag_ids.append(tag.id)
        await self._db.execute(delete(NodeTag).where(NodeTag.node_id == node.id))
        for tid in tag_ids:
            self._db.add(NodeTag(node_id=node.id, tag_id=tid))
        node.updated_by_user_id = actor_id
        await self._db.commit()
        await self._db.refresh(node)
        return node

    async def increment_views(self, node: Node) -> Node:
        if self._repo:
            return await self._repo.increment_views(node)
        node.views = int(node.views or 0) + 1
        await self._db.commit()
        await self._db.refresh(node)
        return node

    async def update_reactions(
        self, node: Node, reaction: str, action: str, actor_id: UUID | None = None
    ) -> Node:
        if self._repo:
            return await self._repo.update_reactions(node, reaction, action, actor_id)
        import json

        raw = node.reactions or {}
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                raw = parsed if isinstance(parsed, dict) else {}
            except Exception:
                raw = {}
        reactions = dict(raw)
        current = int(reactions.get(reaction, 0))
        if action == "add":
            reactions[reaction] = current + 1
        elif action == "remove":
            reactions[reaction] = max(0, current - 1)
        node.reactions = reactions
        if actor_id:
            node.updated_by_user_id = actor_id
        await self._db.commit()
        await self._db.refresh(node)
        return node

    # ------------------------------------------------------------------
    # Bulk operations used by admin services
    async def list_by_author(self, author_id: UUID, workspace_id: UUID, limit: int = 50, offset: int = 0) -> List[Node]:
        res = await self._db.execute(
            select(Node)
            .where(Node.author_id == author_id, Node.workspace_id == workspace_id)
            .order_by(Node.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def bulk_set_visibility(self, node_ids: List[UUID], is_visible: bool, workspace_id: UUID) -> int:
        if not node_ids:
            return 0
        count = 0
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n is None or n.workspace_id != workspace_id:
                continue
            n.is_visible = bool(is_visible)
            count += 1
        await self._db.flush()
        return count

    async def bulk_set_public(self, node_ids: List[UUID], is_public: bool, workspace_id: UUID) -> int:
        if not node_ids:
            return 0
        count = 0
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n is None or n.workspace_id != workspace_id:
                continue
            n.is_public = bool(is_public)
            count += 1
        await self._db.flush()
        return count

    async def bulk_set_tags(self, node_ids: List[UUID], tags: list[str], workspace_id: UUID) -> int:
        if not node_ids:
            return 0
        valid_ids: list[UUID] = []
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n and n.workspace_id == workspace_id:
                valid_ids.append(nid)
        if not valid_ids:
            return 0
        from app.domains.tags.models import Tag
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
        await self._db.execute(delete(NodeTag).where(NodeTag.node_id.in_(valid_ids)))
        for nid in valid_ids:
            for tid in tag_ids:
                self._db.add(NodeTag(node_id=nid, tag_id=tid))
        await self._db.flush()
        return len(valid_ids)

    async def bulk_set_tags_diff(self, node_ids: List[UUID], add: list[str], remove: list[str], workspace_id: UUID) -> int:
        if not node_ids:
            return 0
        valid_ids: list[UUID] = []
        for nid in node_ids:
            n = await self._db.get(Node, nid)
            if n and n.workspace_id == workspace_id:
                valid_ids.append(nid)
        if not valid_ids:
            return 0
        from app.domains.tags.models import Tag
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
        if remove:
            rem_q = await self._db.execute(
                select(Tag.id).where(Tag.slug.in_([s.strip().lower() for s in remove]))
            )
            rem_ids = [row[0] for row in rem_q.all()]
            if rem_ids:
                await self._db.execute(
                    delete(NodeTag).where(
                        NodeTag.node_id.in_(valid_ids), NodeTag.tag_id.in_(rem_ids)
                    )
                )
        for nid in valid_ids:
            for tid in add_ids:
                self._db.add(NodeTag(node_id=nid, tag_id=tid))
        await self._db.flush()
        return len(valid_ids)
