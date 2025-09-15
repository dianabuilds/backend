from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from apps.backendDDD.domains.product.nodes.application.ports import NodeDTO, Repo


@dataclass
class _Node:
    id: int
    author_id: str
    title: str | None
    tags: list[str]
    is_public: bool


class MemoryNodesRepo(Repo):
    def __init__(self) -> None:
        self._nodes: dict[int, _Node] = {}

    def get(self, node_id: int) -> NodeDTO | None:
        n = self._nodes.get(int(node_id))
        if not n:
            return None
        return NodeDTO(
            id=n.id,
            author_id=n.author_id,
            title=n.title,
            tags=list(n.tags),
            is_public=n.is_public,
        )

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        n = self._nodes.get(int(node_id))
        if not n:
            raise ValueError("node not found")
        n.tags = list(tags)
        return self.get(node_id)  # type: ignore[return-value]

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]:
        items = [n for n in self._nodes.values() if n.author_id == author_id]
        items.sort(key=lambda x: (x.id))
        sliced = items[offset : offset + limit]
        return [
            NodeDTO(
                id=n.id,
                author_id=n.author_id,
                title=n.title,
                tags=list(n.tags),
                is_public=n.is_public,
            )
            for n in sliced
        ]

    # helpers for tests/bootstrapping
    def upsert(
        self,
        node_id: int,
        author_id: str,
        title: str | None,
        tags: Sequence[str],
        is_public: bool,
    ) -> None:
        self._nodes[int(node_id)] = _Node(
            id=int(node_id),
            author_id=str(author_id),
            title=title,
            tags=list(tags),
            is_public=bool(is_public),
        )

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
    ) -> NodeDTO:
        new_id = max(self._nodes.keys() or [0]) + 1
        self._nodes[new_id] = _Node(
            id=new_id,
            author_id=str(author_id),
            title=title,
            tags=list(tags or []),
            is_public=bool(is_public),
        )
        return self.get(new_id)  # type: ignore[return-value]

    async def update(
        self, node_id: int, *, title: str | None = None, is_public: bool | None = None
    ) -> NodeDTO:
        n = self._nodes.get(int(node_id))
        if not n:
            raise ValueError("node not found")
        if title is not None:
            n.title = title
        if is_public is not None:
            n.is_public = bool(is_public)
        return self.get(node_id)  # type: ignore[return-value]

    async def delete(self, node_id: int) -> bool:
        return self._nodes.pop(int(node_id), None) is not None
