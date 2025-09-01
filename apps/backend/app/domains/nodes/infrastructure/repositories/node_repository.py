"""Concrete implementation of :class:`INodeRepository`.

The original project relied on a legacy repository located in
``app.repositories``.  In this kata the legacy module is absent which caused
import errors and, as a consequence, any router depending on the repository was
silently skipped.  The admin and public node APIs therefore responded with 404.

This adapter re‑implements the small subset of functionality needed by the
current tests using plain SQLAlchemy queries.  If the legacy repository becomes
available the adapter will delegate to it automatically.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.nodes.infrastructure.models.node import Node
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
    async def get_by_slug(
        self, slug: str, workspace_id: UUID | None = None
    ) -> Node | None:
        if self._repo and workspace_id is not None:
            return await self._repo.get_by_slug(slug, workspace_id=workspace_id)
        query = select(Node).where(Node.slug == slug)
        if workspace_id is None:
            query = query.where(Node.workspace_id.is_(None))
        else:
            query = query.where(Node.workspace_id == workspace_id)
        res = await self._db.execute(query)
        return res.scalar_one_or_none()

    async def get_by_id(
        self, node_id: int, workspace_id: UUID | None
    ) -> Node | None:
        """Fetch node by numeric primary key."""
        if self._repo and workspace_id is not None:
            # The legacy repository uses UUID identifiers; fall back to direct query
            try:
                return await self._repo.get_by_id(node_id, workspace_id=workspace_id)  # type: ignore[arg-type]
            except Exception:
                pass
        query = select(Node).where(Node.id == node_id)
        if workspace_id is None:
            query = query.where(Node.workspace_id.is_(None))
        else:
            query = query.where(Node.workspace_id == workspace_id)
        res = await self._db.execute(query)
        return res.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Mutating operations
    async def create(
        self, payload: NodeCreate, author_id: UUID, workspace_id: UUID | None
    ) -> Node:
        if self._repo and workspace_id is not None:
            return await self._repo.create(payload, author_id, workspace_id)
        node = Node(
            title=payload.title,
            author_id=author_id,
            workspace_id=workspace_id,
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
        loaded = await self.get_by_id(node.id, workspace_id)
        return loaded  # type: ignore[return-value]

    async def update(self, node: Node, payload: NodeUpdate, actor_id: UUID) -> Node:
        if self._repo:
            return await self._repo.update(node, payload, actor_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(node, field, value)
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = actor_id
        await self._db.commit()
        loaded = await self.get_by_id(node.id, node.workspace_id)
        return loaded  # type: ignore[return-value]

    async def delete(self, node: Node) -> None:
        if self._repo:
            await self._repo.delete(node)
            return
        await self._db.delete(node)
        await self._db.commit()

    async def increment_views(self, node: Node) -> Node:
        if self._repo:
            return await self._repo.increment_views(node)
        node.views = int(node.views or 0) + 1
        await self._db.commit()
        loaded = await self.get_by_id(node.id, node.workspace_id)
        return loaded  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Bulk operations used by admin services
    async def list_by_author(
        self,
        author_id: UUID,
        workspace_id: UUID | None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Node]:
        query = select(Node).where(Node.author_id == author_id)
        if workspace_id is None:
            query = query.where(Node.workspace_id.is_(None))
        else:
            query = query.where(Node.workspace_id == workspace_id)
        query = (
            query.order_by(Node.created_at.desc()).offset(offset).limit(limit)
        )
        res = await self._db.execute(query)
        return list(res.scalars().all())

    async def bulk_set_visibility(
        self, node_ids: list[UUID], is_visible: bool, workspace_id: UUID | None
    ) -> int:
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
