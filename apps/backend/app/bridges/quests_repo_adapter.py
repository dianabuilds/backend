from __future__ import annotations

from typing import List, Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.domains.quests_v2.models import QuestV2
from apps.backendDDD.domains.product.quests.application.ports import CreateQuestInput, QuestDTO


class SAQuestsRepo:
    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _dto(self, q: QuestV2) -> QuestDTO:
        return QuestDTO(
            id=str(q.id),
            author_id=str(q.author_id),
            slug=str(q.slug),
            title=q.title,
            description=q.description,
            tags=list(q.tags or []),
            is_public=bool(q.is_public),
        )

    def get(self, quest_id: str) -> QuestDTO | None:
        with self._Session() as s:  # type: Session
            q = s.get(QuestV2, quest_id)
            return self._dto(q) if q else None

    def get_by_slug(self, slug: str) -> QuestDTO | None:
        with self._Session() as s:
            q = s.execute(sa.select(QuestV2).where(QuestV2.slug == slug)).scalar_one_or_none()
            return self._dto(q) if q else None

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0) -> List[QuestDTO]:
        with self._Session() as s:
            q = s.execute(
                sa.select(QuestV2)
                .where(QuestV2.author_id == author_id)
                .order_by(QuestV2.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return [self._dto(row[0]) for row in q.all()]

    def create(self, data: CreateQuestInput, slug: str) -> QuestDTO:
        with self._Session() as s:
            q = QuestV2(
                author_id=data.author_id,
                slug=slug,
                title=data.title,
                description=data.description,
                is_public=bool(data.is_public),
                tags=list(data.tags or []),
            )
            s.add(q)
            s.commit()
            s.refresh(q)
            return self._dto(q)

    def set_tags(self, quest_id: str, tags: Sequence[str]) -> QuestDTO:
        with self._Session() as s:
            q = s.get(QuestV2, quest_id)
            if not q:
                raise ValueError("quest not found")
            q.tags = list(tags)
            s.commit()
            s.refresh(q)
            return self._dto(q)

    def update(self, quest_id: str, *, title: str | None, description: str | None, is_public: bool | None) -> QuestDTO:
        with self._Session() as s:
            q = s.get(QuestV2, quest_id)
            if not q:
                raise ValueError("quest not found")
            if title is not None:
                q.title = title
            if description is not None:
                q.description = description
            if is_public is not None:
                q.is_public = bool(is_public)
            s.commit()
            s.refresh(q)
            return self._dto(q)

