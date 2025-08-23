from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.quests.infrastructure.models.quest_version_models import QuestGraphNode
from app.domains.quests.infrastructure.models.quest_models import QuestProgress
from app.domains.users.infrastructure.models.user import User
from app.domains.quests.access import can_view, can_start


async def start_quest(db: AsyncSession, *, quest_id: UUID, user: User) -> QuestProgress:
    res = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = res.scalars().first()
    if not quest or quest.is_draft:
        raise ValueError("Quest not found")
    if not await can_start(db, quest=quest, user=user):
        raise PermissionError("No access")
    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest.id,
            QuestProgress.user_id == user.id,
            QuestProgress.workspace_id == quest.workspace_id,
        )
    )
    progress = res.scalars().first()
    if progress:
        progress.current_node_id = quest.entry_node_id
        progress.started_at = datetime.utcnow()
    else:
        progress = QuestProgress(
            quest_id=quest.id,
            user_id=user.id,
            workspace_id=quest.workspace_id,
            current_node_id=quest.entry_node_id,
        )
        db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


async def get_progress(db: AsyncSession, *, quest_id: UUID, user: User) -> QuestProgress:
    qres = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = qres.scalars().first()
    if not quest or quest.is_draft:
        raise ValueError("Quest not found")
    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest_id,
            QuestProgress.user_id == user.id,
            QuestProgress.workspace_id == quest.workspace_id,
        )
    )
    progress = res.scalars().first()
    if not progress:
        raise ValueError("Progress not found")
    return progress


async def get_node(db: AsyncSession, *, quest_id: UUID, node_id: UUID, user: User) -> Node:
    res = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = res.scalars().first()
    if not quest or quest.is_draft:
        raise ValueError("Quest not found")
    if not await can_view(db, quest=quest, user=user):
        raise PermissionError("No access")
    # Имеется ли узел в графе квеста (если используется версия графа — можно проверить через таблицу узлов версии)
    # Здесь базовая проверка: напрямую загрузим Node и обновим прогресс
    res = await db.execute(select(Node).where(Node.id == node_id))
    node = res.scalars().first()
    if not node:
        raise ValueError("Node not found")

    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest.id,
            QuestProgress.user_id == user.id,
            QuestProgress.workspace_id == quest.workspace_id,
        )
    )
    progress = res.scalars().first()
    if progress:
        progress.current_node_id = node.id
        progress.updated_at = datetime.utcnow()
        await db.commit()
    return node
