from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class NodeDTO:
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


@runtime_checkable
class Repo(Protocol):
    def get(self, node_id: int) -> NodeDTO | None: ...
    def get_by_slug(self, slug: str) -> NodeDTO | None: ...
    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO: ...
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]: ...

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
    ) -> NodeDTO: ...

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
    ) -> NodeDTO: ...

    async def delete(self, node_id: int) -> bool: ...


@runtime_checkable
class TagCatalog(Protocol):
    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class UsageProjection(Protocol):
    def apply_diff(self, author_id: str, added: Sequence[str], removed: Sequence[str]) -> None: ...
