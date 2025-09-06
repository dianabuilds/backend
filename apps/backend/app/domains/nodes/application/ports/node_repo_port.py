from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domains.nodes.infrastructure.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate


class INodeRepository(Protocol):
    async def get_by_slug(self, slug: str, account_id: int) -> Node | None:  # pragma: no cover
        ...

    async def get_by_id(self, node_id: int, account_id: int) -> Node | None:  # pragma: no cover
        ...

    async def create(
        self, payload: NodeCreate, author_id: UUID, account_id: int
    ) -> Node:  # pragma: no cover
        ...

    async def update(
        self, node: Node, payload: NodeUpdate, actor_id: UUID
    ) -> Node:  # pragma: no cover
        ...

    async def delete(self, node: Node) -> None:  # pragma: no cover
        ...

    async def increment_views(self, node: Node) -> Node:  # pragma: no cover
        ...

    # Дополнительные кейсы
    async def list_by_author(
        self,
        author_id: UUID,
        account_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Node]:  # pragma: no cover
        ...

    async def bulk_set_visibility(
        self, node_ids: list[int], is_visible: bool, account_id: int
    ) -> int:  # pragma: no cover
        ...
