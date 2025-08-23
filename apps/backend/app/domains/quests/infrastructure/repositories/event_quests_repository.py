from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quests.application.ports.event_quests_port import (
    IEventQuestsRepository,
)
from app.domains.quests.infrastructure.models.event_quest_models import (
    EventQuest,
    EventQuestCompletion,
)


class EventQuestsRepository(IEventQuestsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_active_for_node(
        self, workspace_id, now: datetime, node_id
    ) -> Sequence[EventQuest]:
        result = await self._db.execute(
            select(EventQuest).where(
                EventQuest.workspace_id == workspace_id,
                EventQuest.is_active == True,  # noqa: E712
                EventQuest.target_node_id == node_id,
                EventQuest.starts_at <= now,
                EventQuest.expires_at >= now,
            )
        )
        return list(result.scalars().all())

    async def has_completion(self, quest_id, user_id, workspace_id) -> bool:
        res = await self._db.execute(
            select(EventQuestCompletion).where(
                EventQuestCompletion.quest_id == quest_id,
                EventQuestCompletion.user_id == user_id,
                EventQuestCompletion.workspace_id == workspace_id,
            )
        )
        return res.scalars().first() is not None

    async def create_completion(
        self, quest_id, user_id, node_id, workspace_id
    ) -> EventQuestCompletion:
        completion = EventQuestCompletion(
            quest_id=quest_id,
            user_id=user_id,
            node_id=node_id,
            workspace_id=workspace_id,
        )
        self._db.add(completion)
        await self._db.commit()
        await self._db.refresh(completion)
        return completion

    async def count_completions(self, quest_id, workspace_id) -> int:
        count_res = await self._db.execute(
            select(func.count(EventQuestCompletion.id)).where(
                EventQuestCompletion.quest_id == quest_id,
                EventQuestCompletion.workspace_id == workspace_id,
            )
        )
        return int(count_res.scalar_one())
