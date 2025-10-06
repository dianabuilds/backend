from __future__ import annotations

import uuid
from collections.abc import Sequence

from domains.product.quests.application.ports import (
    CreateQuestInput,
    QuestDTO,
    Repo,
)


class MemoryQuestsRepo(Repo):
    def __init__(self) -> None:
        self._by_id: dict[str, QuestDTO] = {}
        self._by_slug: dict[str, str] = {}

    def get(self, quest_id: str) -> QuestDTO | None:
        return self._by_id.get(str(quest_id))

    def get_by_slug(self, slug: str) -> QuestDTO | None:
        qid = self._by_slug.get(str(slug))
        return self._by_id.get(qid) if qid else None

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[QuestDTO]:
        items = [q for q in self._by_id.values() if q.author_id == str(author_id)]
        items.sort(key=lambda x: x.id)
        return items[offset : offset + limit]

    def create(self, data: CreateQuestInput, slug: str) -> QuestDTO:
        qid = str(uuid.uuid4())
        dto = QuestDTO(
            id=qid,
            author_id=str(data.author_id),
            slug=str(slug),
            title=str(data.title),
            description=data.description,
            tags=list(data.tags or []),
            is_public=bool(data.is_public),
        )
        self._by_id[qid] = dto
        self._by_slug[dto.slug] = qid
        return dto

    def set_tags(self, quest_id: str, tags: Sequence[str]) -> QuestDTO:
        q = self._by_id.get(str(quest_id))
        if not q:
            raise ValueError("quest not found")
        dto = QuestDTO(
            id=q.id,
            author_id=q.author_id,
            slug=q.slug,
            title=q.title,
            description=q.description,
            tags=list(tags),
            is_public=q.is_public,
        )
        self._by_id[q.id] = dto
        return dto

    def update(
        self,
        quest_id: str,
        *,
        title: str | None,
        description: str | None,
        is_public: bool | None,
    ) -> QuestDTO:
        q = self._by_id.get(str(quest_id))
        if not q:
            raise ValueError("quest not found")
        dto = QuestDTO(
            id=q.id,
            author_id=q.author_id,
            slug=q.slug,
            title=title if title is not None else q.title,
            description=description if description is not None else q.description,
            tags=list(q.tags),
            is_public=bool(is_public) if is_public is not None else q.is_public,
        )
        self._by_id[q.id] = dto
        return dto


MemoryRepo = MemoryQuestsRepo
