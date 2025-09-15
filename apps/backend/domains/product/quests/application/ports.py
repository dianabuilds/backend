from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class QuestDTO:
    id: str
    author_id: str
    slug: str
    title: str
    description: str | None
    tags: Sequence[str]
    is_public: bool


@dataclass(frozen=True)
class CreateQuestInput:
    author_id: str
    title: str
    description: str | None = None
    tags: Sequence[str] = ()
    is_public: bool = False


@runtime_checkable
class Repo(Protocol):
    def get(self, quest_id: str) -> QuestDTO | None: ...
    def get_by_slug(self, slug: str) -> QuestDTO | None: ...
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[QuestDTO]: ...
    def create(self, data: CreateQuestInput, slug: str) -> QuestDTO: ...
    def set_tags(self, quest_id: str, tags: Sequence[str]) -> QuestDTO: ...
    def update(
        self,
        quest_id: str,
        *,
        title: str | None,
        description: str | None,
        is_public: bool | None,
    ) -> QuestDTO: ...


@runtime_checkable
class TagCatalog(Protocol):
    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...
