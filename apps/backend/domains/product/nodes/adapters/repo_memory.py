from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import dataclass

from domains.product.nodes.application.ports import NodeDTO, Repo


@dataclass
class _Node:
    id: int
    slug: str
    author_id: str
    title: str | None
    tags: list[str]
    is_public: bool
    status: str | None = None
    publish_at: str | None = None
    unpublish_at: str | None = None
    content_html: str | None = None
    cover_url: str | None = None
    embedding: list[float] | None = None
    views_count: int = 0
    reactions_like_count: int = 0
    comments_disabled: bool = False
    comments_locked_by: str | None = None
    comments_locked_at: str | None = None


class MemoryNodesRepo(Repo):
    def __init__(self) -> None:
        self._nodes: dict[int, _Node] = {}

    def get(self, node_id: int) -> NodeDTO | None:
        node = self._nodes.get(int(node_id))
        return self._to_dto(node) if node else None

    def get_by_slug(self, slug: str) -> NodeDTO | None:
        for node in self._nodes.values():
            if node.slug == slug:
                return self._to_dto(node)
        return None

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        node = self._nodes.get(int(node_id))
        if node is None:
            raise ValueError("node not found")
        node.tags = list(tags)
        return self._to_dto(node)

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]:
        items = [node for node in self._nodes.values() if node.author_id == author_id]
        items.sort(key=lambda n: n.id)
        sliced = items[offset : offset + limit]
        return [self._to_dto(node) for node in sliced]

    # helpers for tests/bootstrapping
    def upsert(
        self,
        node_id: int,
        author_id: str,
        title: str | None,
        tags: Sequence[str],
        is_public: bool,
        *,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
        views_count: int = 0,
        reactions_like_count: int = 0,
        comments_disabled: bool = False,
        comments_locked_by: str | None = None,
        comments_locked_at: str | None = None,
    ) -> None:
        slug = secrets.token_hex(8)
        self._nodes[int(node_id)] = _Node(
            id=int(node_id),
            slug=slug,
            author_id=str(author_id),
            title=title,
            tags=list(tags),
            is_public=bool(is_public),
            status=status,
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
            embedding=list(embedding) if embedding is not None else None,
            views_count=int(views_count),
            reactions_like_count=int(reactions_like_count),
            comments_disabled=bool(comments_disabled),
            comments_locked_by=(
                str(comments_locked_by) if comments_locked_by is not None else None
            ),
            comments_locked_at=comments_locked_at,
        )

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
        views_count: int = 0,
        reactions_like_count: int = 0,
        comments_disabled: bool = False,
        comments_locked_by: str | None = None,
        comments_locked_at: str | None = None,
    ) -> NodeDTO:
        new_id = max(self._nodes.keys() or [0]) + 1
        # naive uniqueness check in memory (extremely unlikely collision)
        while True:
            slug = secrets.token_hex(8)
            if all(node.slug != slug for node in self._nodes.values()):
                break
        self._nodes[new_id] = _Node(
            id=new_id,
            slug=slug,
            author_id=str(author_id),
            title=title,
            tags=list(tags or []),
            is_public=bool(is_public),
            status=(
                status
                if status is not None
                else ("published" if is_public else "draft")
            ),
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
            embedding=list(embedding) if embedding is not None else None,
            views_count=int(views_count),
            reactions_like_count=int(reactions_like_count),
            comments_disabled=bool(comments_disabled),
            comments_locked_by=(
                str(comments_locked_by) if comments_locked_by is not None else None
            ),
            comments_locked_at=comments_locked_at,
        )
        return self._to_dto(self._nodes[new_id])

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
        node = self._nodes.get(int(node_id))
        if node is None:
            raise ValueError("node not found")
        if title is not None:
            node.title = title
        if is_public is not None:
            node.is_public = bool(is_public)
        if status is not None:
            node.status = status
        if publish_at is not None:
            node.publish_at = publish_at
        if unpublish_at is not None:
            node.unpublish_at = unpublish_at
        if content_html is not None:
            node.content_html = content_html
        if cover_url is not None:
            node.cover_url = cover_url
        if embedding is not None:
            node.embedding = list(embedding)
        return self._to_dto(node)

    async def delete(self, node_id: int) -> bool:
        node = self._nodes.get(int(node_id))
        if node is None:
            return False
        node.status = "deleted"
        node.is_public = False
        return True

    async def _araw_get_by_slug(self, slug: str) -> NodeDTO | None:
        return self.get_by_slug(slug)

    async def _araw_get(self, node_id: int) -> NodeDTO | None:
        return self.get(node_id)

    async def _aset_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        return self.set_tags(node_id, tags)

    @staticmethod
    def _to_dto(node: _Node) -> NodeDTO:
        return NodeDTO(
            id=node.id,
            slug=node.slug,
            author_id=node.author_id,
            title=node.title,
            tags=list(node.tags),
            is_public=node.is_public,
            status=node.status,
            publish_at=node.publish_at,
            unpublish_at=node.unpublish_at,
            content_html=node.content_html,
            cover_url=node.cover_url,
            embedding=list(node.embedding) if node.embedding is not None else None,
            views_count=int(node.views_count),
            reactions_like_count=int(node.reactions_like_count),
            comments_disabled=bool(node.comments_disabled),
            comments_locked_by=node.comments_locked_by,
            comments_locked_at=node.comments_locked_at,
        )

    async def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> list[NodeDTO]:
        norm = self._normalize_vector(embedding)
        if norm is None:
            return []
        scored: list[tuple[float, _Node]] = []
        for node in self._nodes.values():
            if not node.is_public or node.embedding is None:
                continue
            target = self._normalize_vector(node.embedding)
            if target is None or len(target) != len(norm):
                continue
            score = self._dot(norm, target)
            if score <= 0.0:
                continue
            scored.append((score, node))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [self._to_dto(node) for score, node in scored[:limit]]

    @staticmethod
    def _normalize_vector(values: Sequence[float] | None) -> list[float] | None:
        if values is None:
            return None
        acc = [float(v) for v in values]
        norm = sum(v * v for v in acc) ** 0.5
        if norm <= 0:
            return None
        return [v / norm for v in acc]

    @staticmethod
    def _dot(a: Sequence[float], b: Sequence[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=False))
