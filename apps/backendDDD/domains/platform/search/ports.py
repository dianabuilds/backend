from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Doc:
    id: str
    title: str
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Hit:
    id: str
    score: float
    title: str
    tags: tuple[str, ...]


class IndexPort(Protocol):
    async def upsert(self, doc: Doc) -> None: ...
    async def delete(self, id: str) -> None: ...  # noqa: A002 - id name OK here
    async def list_all(self) -> list[Doc]: ...


class QueryPort(Protocol):
    async def search(
        self, q: str, *, tags: Sequence[str] | None, match: str, limit: int, offset: int
    ) -> list[Hit]: ...


class SearchCache(Protocol):
    async def get(self, key: str) -> list[Hit] | None: ...
    async def set(self, key: str, hits: list[Hit]) -> None: ...
    async def bump_version(self) -> None: ...
    async def versioned_key(self, raw_key: str) -> str: ...


class SearchPersistence(Protocol):
    async def load(self) -> list[Doc]: ...
    async def save(self, docs: list[Doc]) -> None: ...


__all__ = ["Doc", "Hit", "IndexPort", "QueryPort", "SearchCache", "SearchPersistence"]
