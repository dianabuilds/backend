from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem


class ITagSyncService(Protocol):
    def normalize(self, data: dict[str, Any]) -> list[str] | None:  # pragma: no cover
        ...

    async def sync(
        self, db: AsyncSession, *, item: NodeItem, node: Node, tags: list[str] | None
    ) -> bool:  # pragma: no cover
        ...


__all__ = ["ITagSyncService"]

