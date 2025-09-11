"""Concrete SQLAlchemy implementation of :class:`INodeRepository`.

Provides the minimal set of operations required by the current tests without
any dependency on the legacy repository implementation.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from uuid import UUID

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.models.node_version import NodeVersion
from app.domains.nodes.models import NodeItem
from app.schemas.node import NodeCreate, NodeUpdate


class NodeRepository(INodeRepository):
    """Repository used by API endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._hex_re = re.compile(r"[a-f0-9]{16}")

    async def _unique_slug_for_author(
        self,
        base: str,
        author_id: UUID,
        *,
        skip_id: int | None = None,
    ) -> str:
        slug_base = slugify(base) or "node"
        idx = 0
        while True:
            text = slug_base if idx == 0 else f"{slug_base}-{idx}"
            candidate = hashlib.sha256(text.encode()).hexdigest()[:16]
            res = await self._db.execute(
                select(Node).where(Node.slug == candidate, Node.author_id == author_id)
            )
            existing = res.scalar_one_or_none()
            if not existing or existing.id == skip_id:
                return candidate
            idx += 1

    # ------------------------------------------------------------------
    # Basic getters
    async def get_by_slug(self, slug: str) -> Node | None:
        """Fetch node by slug (profile-centric semantics)."""
        stmt = (
            select(Node)
            .join(NodeItem, NodeItem.node_id == Node.id)
            .options(selectinload(Node.tags))
            .where(Node.slug == slug)
        )
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug_for_author(self, slug: str, author_id: UUID) -> Node | None:
        query = (
            select(Node)
            .options(selectinload(Node.tags))
            .where(Node.slug == slug, Node.author_id == author_id)
        )
        res = await self._db.execute(query)
        return res.scalar_one_or_none()

    async def get_version(self, node_id: int, version: int) -> NodeVersion | None:
        """Return stored snapshot for a node version."""
        res = await self._db.execute(
            select(NodeVersion).where(
                NodeVersion.node_id == node_id, NodeVersion.version == version
            )
        )
        return res.scalar_one_or_none()

    async def get_by_id(self, node_id: int) -> Node | None:
        """Fetch node by id (profile-centric semantics)."""
        stmt = (
            select(Node)
            .join(NodeItem, NodeItem.node_id == Node.id)
            .options(selectinload(Node.tags))
            .where(Node.id == node_id)
        )
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_simple(self, node_id: int) -> Node | None:
        query = select(Node).options(selectinload(Node.tags)).where(Node.id == node_id)
        res = await self._db.execute(query)
        return res.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Mutating operations
    async def create(self, payload: NodeCreate, author_id: UUID) -> Node:
        candidate = (payload.slug or "").strip().lower()
        if candidate and self._hex_re.fullmatch(candidate):
            res = await self._db.execute(
                select(Node).where(Node.slug == candidate, Node.author_id == author_id)
            )
            if res.scalar_one_or_none():
                candidate = await self._unique_slug_for_author(candidate, author_id)
        else:
            base = candidate or (payload.title or "node")
            candidate = await self._unique_slug_for_author(base, author_id)

        node = Node(
            title=payload.title,
            slug=candidate,
            author_id=author_id,
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
        await self._db.commit()
        loaded = await self.get_by_id_simple(node.id)
        return loaded  # type: ignore[return-value]

    async def create_personal(self, payload: NodeCreate, author_id: UUID) -> Node:

        candidate = (payload.slug or "").strip().lower()
        if candidate and self._hex_re.fullmatch(candidate):
            res = await self._db.execute(
                select(Node).where(Node.slug == candidate, Node.author_id == author_id)
            )
            if res.scalar_one_or_none():
                candidate = await self._unique_slug_for_author(candidate, author_id)
        else:
            base = candidate or (payload.title or "node")
            candidate = await self._unique_slug_for_author(base, author_id)

        node = Node(
            title=payload.title,
            slug=candidate,
            author_id=author_id,
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
        await self._db.commit()
        loaded = await self.get_by_id_simple(node.id)
        return loaded  # type: ignore[return-value]

    async def update(self, node: Node, payload: NodeUpdate, actor_id: UUID) -> Node:
        data = payload.model_dump(exclude_unset=True)
        slug_candidate = data.pop("slug", None)
        # Handle content and cover URL updates stored in Node.meta
        if "content" in data:
            try:
                node.content = data.pop("content")  # type: ignore[assignment]
            except Exception:
                pass
        if "cover_url" in data:
            try:
                node.cover_url = data.pop("cover_url")  # type: ignore[assignment]
            except Exception:
                pass
        for field, value in data.items():
            setattr(node, field, value)
        if slug_candidate is not None:
            candidate = (slug_candidate or "").strip().lower()
            if candidate and self._hex_re.fullmatch(candidate):
                res = await self._db.execute(
                    select(Node).where(
                        Node.slug == candidate, Node.author_id == node.author_id, Node.id != node.id
                    )
                )
                if res.scalar_one_or_none():
                    candidate = await self._unique_slug_for_author(
                        candidate, node.author_id, skip_id=node.id
                    )
            else:
                base = candidate or data.get("title") or node.title or "node"
                candidate = await self._unique_slug_for_author(
                    base, node.author_id, skip_id=node.id
                )
            node.slug = candidate
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = actor_id
        node.version = int(node.version or 1) + 1
        snapshot = None
        try:
            snapshot = NodeVersion(
                node_id=node.id,
                version=node.version,
                title=node.title,
                meta=node.meta or {},
                created_at=node.updated_at,
                created_by_user_id=str(actor_id),
            )
            self._db.add(snapshot)
        except Exception:
            snapshot = None
        saved_id = node.id
        try:
            await self._db.commit()
        except Exception:
            # Retry commit without snapshot if snapshot caused failure
            await self._db.rollback()
            if snapshot is not None:
                try:
                    self._db.expunge(snapshot)
                except Exception:
                    pass
            # Reapply changes and commit only node updates
            for field, value in data.items():
                setattr(node, field, value)
            try:
                from datetime import datetime as _dt

                node.updated_at = _dt.utcnow()
            except Exception:
                pass
            await self._db.commit()
        loaded = await self.get_by_id_simple(saved_id)
        return loaded  # type: ignore[return-value]

    async def rollback(self, node: Node, version: int, actor_id: UUID) -> Node:
        """Rollback node state to a specific version."""
        snap = await self.get_version(node.id, version)
        if not snap:
            raise ValueError("Version not found")

        node.title = snap.title
        node.meta = snap.meta or {}
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = actor_id
        node.version = int(node.version or 1) + 1

        new_snap = NodeVersion(
            node_id=node.id,
            version=node.version,
            title=node.title,
            meta=node.meta or {},
            created_at=node.updated_at,
            created_by_user_id=str(actor_id),
        )
        self._db.add(new_snap)
        await self._db.commit()
        loaded = await self.get_by_id_simple(node.id)
        return loaded  # type: ignore[return-value]

    async def delete(self, node: Node) -> None:
        await self._db.delete(node)
        await self._db.commit()

    async def increment_views(self, node: Node) -> Node:
        node.views = int(node.views or 0) + 1
        await self._db.commit()
        loaded = await self.get_by_id_simple(node.id)
        return loaded  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Bulk operations used by admin services
    async def list_by_author(
        self,
        author_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Node]:
        query = (
            select(Node)
            .where(Node.author_id == author_id)
            .order_by(Node.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self._db.execute(query)
        return list(res.scalars().all())

    async def bulk_set_visibility(self, node_ids: list[int], is_visible: bool) -> int:
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
