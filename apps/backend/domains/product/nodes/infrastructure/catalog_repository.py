from __future__ import annotations

import inspect
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from domains.product.nodes.application.ports import NodeDTO, Repo


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


@dataclass
class CatalogRepository:
    repo: Repo

    async def get(self, node_id: int) -> NodeDTO | None:
        return await _maybe_await(self.repo.get(node_id))

    async def get_by_slug(self, slug: str) -> NodeDTO | None:
        return await _maybe_await(self.repo.get_by_slug(slug))

    async def set_tags(self, node_id: int, tags: Iterable[str]) -> NodeDTO:
        return await _maybe_await(self.repo.set_tags(node_id, tags))

    async def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]:
        result = await _maybe_await(
            self.repo.list_by_author(author_id, limit=limit, offset=offset)
        )
        return list(result)

    async def delete(self, node_id: int) -> bool:
        result = await _maybe_await(self.repo.delete(node_id))
        return bool(result)

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        tags: Iterable[str] | None,
        is_public: bool,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO:
        return await _maybe_await(
            self.repo.create(
                author_id=author_id,
                title=title,
                tags=tags,
                is_public=is_public,
                status=status,
                publish_at=publish_at,
                unpublish_at=unpublish_at,
                content_html=content_html,
                cover_url=cover_url,
                embedding=embedding,
            )
        )

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
        return await _maybe_await(
            self.repo.update(
                node_id,
                title=title,
                is_public=is_public,
                status=status,
                publish_at=publish_at,
                unpublish_at=unpublish_at,
                content_html=content_html,
                cover_url=cover_url,
                embedding=embedding,
            )
        )
