from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.infrastructure.models.quest_version_models import QuestVersion
from app.domains.users.infrastructure.models.user import User
from app.domains.quests.validation import validate_version_graph


class ValidationFailed(Exception):
    def __init__(self, report: Dict[str, Any]):
        super().__init__("validation_failed")
        self.report = report


async def latest_version(db: AsyncSession, *, quest_id: UUID) -> Optional[QuestVersion]:
    res = await db.execute(
        select(QuestVersion).where(QuestVersion.quest_id == quest_id).order_by(QuestVersion.number.desc())
    )
    return res.scalars().first()


async def create_version(
    db: AsyncSession,
    *,
    quest_id: UUID,
    created_by: Optional[UUID] = None,
    parent_version_id: Optional[UUID] = None,
    status: str = "draft",
) -> QuestVersion:
    """Создать новую версию (без копирования графа; копирование — в будущем)."""
    # Определяем следующий номер
    res = await db.execute(
        select(QuestVersion.number).where(QuestVersion.quest_id == quest_id).order_by(QuestVersion.number.desc())
    )
    last_num = res.scalars().first() or 0
    ver = QuestVersion(
        quest_id=quest_id,
        number=int(last_num) + 1,
        status=status,
        created_by=created_by,
        parent_version_id=parent_version_id,
        meta={},
    )
    db.add(ver)
    await db.flush()
    return ver


async def release_latest(
    db: AsyncSession,
    *,
    quest_id: UUID,
    workspace_id: UUID,
    actor: Optional[User] = None,
) -> Quest:
    """Выпустить (опубликовать) последнюю версию квеста с жёсткой валидацией."""
    # Загружаем квест
    resq = await db.execute(
        select(Quest).where(
            Quest.id == quest_id,
            Quest.workspace_id == workspace_id,
            Quest.is_deleted == False,
        )
    )
    quest = resq.scalars().first()
    if not quest:
        raise ValueError("Quest not found")
    # Проверяем последнюю версию
    ver = await latest_version(db, quest_id=quest_id)
    if ver:
        report = await validate_version_graph(db, ver.id)
        if (report or {}).get("errors"):
            raise ValidationFailed(report)
        # Отметим версию как released
        ver.status = "released"
    # Помечаем квест опубликованным
    quest.is_draft = False
    quest.published_at = datetime.utcnow()
    await db.commit()
    await db.refresh(quest)
    return quest


async def rollback_latest(db: AsyncSession, *, quest_id: UUID, actor: Optional[User] = None) -> QuestVersion | None:
    """Пометить последнюю версию как archived (минимальная реализация отката)."""
    ver = await latest_version(db, quest_id=quest_id)
    if not ver:
        return None
    ver.status = "archived"
    await db.commit()
    await db.refresh(ver)
    return ver
