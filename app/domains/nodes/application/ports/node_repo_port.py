from __future__ import annotations

from typing import Protocol, List
from uuid import UUID

from app.domains.nodes.infrastructure.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate


class INodeRepository(Protocol):
    async def get_by_slug(self, slug: str) -> Node | None:  # pragma: no cover
        ...

    async def get_by_id(self, node_id: UUID) -> Node | None:  # pragma: no cover
        ...

    async def create(self, payload: NodeCreate, author_id: UUID) -> Node:  # pragma: no cover
        ...

    async def update(self, node: Node, payload: NodeUpdate) -> Node:  # pragma: no cover
        ...

    async def delete(self, node: Node) -> None:  # pragma: no cover
        ...

    async def set_tags(self, node: Node, tags: list[str]) -> Node:  # pragma: no cover
        ...

    async def increment_views(self, node: Node) -> Node:  # pragma: no cover
        ...

    async def update_reactions(self, node: Node, reaction: str, action: str) -> Node:  # pragma: no cover
        ...

    # Дополнительные кейсы
    async def list_by_author(self, author_id: UUID, limit: int = 50, offset: int = 0) -> List[Node]:  # pragma: no cover
        ...

    async def bulk_set_visibility(self, node_ids: List[UUID], is_visible: bool) -> int:  # pragma: no cover
        ...

    async def bulk_set_public(self, node_ids: List[UUID], is_public: bool) -> int:  # pragma: no cover
        ...

    async def bulk_set_tags(self, node_ids: List[UUID], tags: list[str]) -> int:  # pragma: no cover
        ...

    async def bulk_set_tags_diff(self, node_ids: List[UUID], add: list[str], remove: list[str]) -> int:  # pragma: no cover
        ...
