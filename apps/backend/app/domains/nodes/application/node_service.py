# mypy: ignore-errors
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import validate_transition
from app.schemas.nodes_common import NodeType, Status, Visibility


class NodeService:
    """Service layer for managing content items."""

    def __init__(self, db: AsyncSession, *args: Any, **kwargs: Any) -> None:
        """Initialize service.

        Extra positional or keyword arguments are ignored.  Older call sites pass
        additional dependencies such as navigation cache or notification ports;
        accepting ``*args``/``**kwargs`` keeps this service compatible while the
        parameters are unused here.
        """

        self._db = db
        self._allowed_types = {NodeType.article.value}

    # ------------------------------------------------------------------
    def _normalize_type(self, node_type: str | NodeType) -> str:
        value = node_type.value if isinstance(node_type, NodeType) else node_type
        if value not in self._allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported node type")
        return value

    # Queries -----------------------------------------------------------------
    async def list(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        node_type = self._normalize_type(node_type)
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type=node_type,
            page=page,
            per_page=per_page,
            q=None,
        )

    async def search(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        q: str,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        node_type = self._normalize_type(node_type)
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type=node_type,
            q=q,
            page=page,
            per_page=per_page,
        )

    async def get(
        self, workspace_id: UUID, node_type: str | NodeType, node_id: UUID
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self._db.get(NodeItem, node_id)
        if not item or item.workspace_id != workspace_id or item.type != node_type:
            raise HTTPException(status_code=404, detail="Node not found")
        await NodePatchDAO.overlay(self._db, [item])
        return item

    # Mutations ---------------------------------------------------------------
    async def create(
        self, workspace_id: UUID, node_type: str | NodeType, *, actor_id: UUID
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await NodeItemDAO.create(
            self._db,
            workspace_id=workspace_id,
            type=node_type,
            slug=f"{node_type}-{uuid4().hex[:8]}",
            title=f"New {node_type}",
            created_by_user_id=actor_id,
        )
        await self._db.commit()
        return item

    async def update(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        data: dict[str, Any],
        *,
        actor_id: UUID,
    ) -> NodeItem:
        if "quest_data" in data:
            raise HTTPException(
                status_code=422,
                detail="quest_data is not supported here; use /quests/*",
            )

        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        if item.status == Status.published:
            item.status = Status.draft
            item.visibility = Visibility.private
            item.published_at = None
        item.updated_by_user_id = actor_id
        item.updated_at = datetime.utcnow()
        await self._db.commit()
        return item

    async def publish(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        *,
        actor_id: UUID,
        access: Literal["everyone", "premium_only", "early_access"] = "everyone",
        cover: str | None = None,
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)
        validate_transition(item.status, Status.published)
        if access == "early_access":
            item.visibility = Visibility.unlisted
        else:
            item.visibility = Visibility.public
        item.status = Status.published
        item.published_at = datetime.utcnow()
        item.updated_by_user_id = actor_id
        node = await self._db.get(Node, node_id)
        if node:
            node.premium_only = access == "premium_only"
            node.is_public = access != "early_access"
            node.visibility = (
                Visibility.unlisted if access == "early_access" else Visibility.public
            )
            if cover is not None:
                node.cover_url = cover
            node.updated_by_user_id = actor_id
            node.updated_at = datetime.utcnow()
        await self._db.commit()
        return item
