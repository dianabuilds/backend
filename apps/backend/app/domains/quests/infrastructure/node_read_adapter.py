from __future__ import annotations

"""Temporary read-only adapter exposing node-like queries for quests."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.models import NodeItem


class QuestNodeReadAdapter:
    """Provide limited read-only access to quest nodes.

    This adapter exists to support the legacy ``/admin/nodes/quest`` endpoints
    until dedicated quest management routes are introduced.  It mirrors a small
    subset of :class:`NodeService` focusing solely on retrieving quest items.
    """

    def __init__(self, db: AsyncSession) -> None:  # pragma: no cover - trivial
        self._db = db

    async def list(
        self,
        workspace_id: UUID,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        """Return paginated quests for a workspace."""

        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type="quest",
            page=page,
            per_page=per_page,
            q=None,
        )

    async def search(
        self,
        workspace_id: UUID,
        q: str,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        """Search quests by title or summary."""

        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type="quest",
            q=q,
            page=page,
            per_page=per_page,
        )

    async def get(self, workspace_id: UUID, node_id: UUID) -> NodeItem:
        """Retrieve a single quest by identifier."""

        item = await self._db.get(NodeItem, node_id)
        if not item or item.workspace_id != workspace_id or item.type != "quest":
            raise HTTPException(status_code=404, detail="Node not found")
        await NodePatchDAO.overlay(self._db, [item])
        return item


__all__ = ["QuestNodeReadAdapter"]

