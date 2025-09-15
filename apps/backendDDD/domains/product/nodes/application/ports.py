from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class NodeDTO:
    id: int
    author_id: str
    title: str | None
    tags: list[str]
    is_public: bool


@runtime_checkable
class Repo(Protocol):
    def get(self, node_id: int) -> NodeDTO | None: ...
    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO: ...
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]: ...

    # New CRUD operations
    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
    ) -> NodeDTO: ...
    async def update(
        self, node_id: int, *, title: str | None = None, is_public: bool | None = None
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
    def apply_diff(
        self, author_id: str, added: Sequence[str], removed: Sequence[str]
    ) -> None: ...
