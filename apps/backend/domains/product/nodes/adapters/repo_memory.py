from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count

from domains.product.nodes.application.ports import NodeDTO


class MemoryNodesRepo:
    """In-memory implementation of the nodes repository for tests."""

    def __init__(self) -> None:
        self._nodes: dict[int, NodeDTO] = {}
        self._slug_index: dict[str, int] = {}
        self._id_seq = count(1)
        self._slug_seq = count(1)

    def _next_slug(self) -> str:
        return f"node-{next(self._slug_seq):x}"

    def _store(self, dto: NodeDTO) -> NodeDTO:
        self._nodes[int(dto.id)] = dto
        self._slug_index[str(dto.slug)] = int(dto.id)
        return dto

    def get(self, node_id: int) -> NodeDTO | None:
        return self._nodes.get(int(node_id))

    def get_by_slug(self, slug: str) -> NodeDTO | None:
        node_id = self._slug_index.get(str(slug))
        if node_id is None:
            return None
        return self._nodes.get(node_id)

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0) -> list[NodeDTO]:
        author = str(author_id)
        items = [dto for dto in self._nodes.values() if dto.author_id == author]
        items.sort(key=lambda dto: dto.id)
        return items[offset : offset + limit]

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        dto = self._nodes.get(int(node_id))
        if dto is None:
            raise ValueError("node_not_found")
        updated = replace(dto, tags=[str(tag) for tag in tags])
        return self._store(updated)

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO:
        node_id = next(self._id_seq)
        slug = self._next_slug()
        dto = NodeDTO(
            id=node_id,
            slug=slug,
            author_id=str(author_id),
            title=title,
            tags=[str(tag) for tag in (tags or [])],
            is_public=bool(is_public),
            status=status,
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
            embedding=list(embedding) if embedding is not None else None,
        )
        return self._store(dto)

    async def update(
        self,
        node_id: int,
        *,
        title: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO:
        dto = self._nodes.get(int(node_id))
        if dto is None:
            raise ValueError("node_not_found")
        updated = replace(
            dto,
            title=dto.title if title is None else title,
            is_public=dto.is_public if is_public is None else bool(is_public),
            status=dto.status if status is None else status,
            publish_at=dto.publish_at if publish_at is None else publish_at,
            unpublish_at=dto.unpublish_at if unpublish_at is None else unpublish_at,
            content_html=dto.content_html if content_html is None else content_html,
            cover_url=dto.cover_url if cover_url is None else cover_url,
            embedding=(dto.embedding if embedding is None else list(embedding)),
        )
        return self._store(updated)

    async def delete(self, node_id: int) -> bool:
        removed = self._nodes.pop(int(node_id), None)
        if removed is None:
            return False
        self._slug_index.pop(str(removed.slug), None)
        return True

    async def _aset_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        return self.set_tags(node_id, tags)

    async def _araw_get(self, node_id: int) -> NodeDTO | None:
        return self.get(node_id)

    async def _araw_get_by_slug(self, slug: str) -> NodeDTO | None:
        return self.get_by_slug(slug)


__all__ = ["MemoryNodesRepo"]
