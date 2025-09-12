from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node


class INodeCacheInvalidation(Protocol):
    async def invalidate_for_node(self, db: AsyncSession, node: Node) -> None:  # pragma: no cover
        ...

    async def invalidate_by_user(self, user_id: UUID) -> None:  # pragma: no cover
        ...

    async def invalidate_compass_by_user(self, user_id: UUID) -> None:  # pragma: no cover
        ...


__all__ = ["INodeCacheInvalidation"]

