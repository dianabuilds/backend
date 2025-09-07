from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.achievements.application.ports.repository import (
    IAchievementsRepository,
)
from app.domains.achievements.infrastructure.models.achievement_models import (
    Achievement,
    UserAchievement,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.models.event_counter import UserEventCounter


class AchievementsRepository(IAchievementsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # User achievements
    async def user_has_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> bool:
        res = await self._db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
                (UserAchievement.account_id == workspace_id),
            )
        )
        return res.scalars().first() is not None

    async def get_achievement(self, achievement_id: UUID, workspace_id: UUID) -> Achievement | None:
        res = await self._db.execute(
            select(Achievement).where(
                Achievement.id == achievement_id,
                (Achievement.account_id == workspace_id),
            )
        )
        return res.scalars().first()

    async def add_user_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> None:
        self._db.add(
            UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                account_id=workspace_id,
            )
        )

    async def delete_user_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> bool:
        res = await self._db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
                (UserAchievement.account_id == workspace_id),
            )
        )
        ua = res.scalars().first()
        if not ua:
            return False
        await self._db.delete(ua)
        return True

    async def list_user_achievements(
        self, user_id: UUID, workspace_id: UUID
    ) -> list[tuple[Achievement, UserAchievement | None]]:
        res = await self._db.execute(
            select(Achievement, UserAchievement)
            .outerjoin(
                UserAchievement,
                (UserAchievement.achievement_id == Achievement.id)
                & (UserAchievement.user_id == user_id),
            )
            .where(Achievement.account_id == workspace_id)
            .order_by(Achievement.title.asc())
        )
        return list(res.all())

    # Counters/conditions
    async def increment_counter(self, user_id: UUID, key: str, workspace_id: UUID) -> None:
        res = await self._db.execute(
            select(UserEventCounter).where(
                UserEventCounter.user_id == user_id,
                UserEventCounter.event == key,
                UserEventCounter.account_id == workspace_id,
            )
        )
        counter = res.scalars().first()
        if counter:
            counter.count += 1
        else:
            self._db.add(
                UserEventCounter(
                    user_id=user_id,
                    event=key,
                    workspace_id=workspace_id,
                    count=1,
                )
            )

    async def get_counter(self, user_id: UUID, key: str, workspace_id: UUID) -> int:
        res = await self._db.execute(
            select(UserEventCounter.count).where(
                UserEventCounter.user_id == user_id,
                UserEventCounter.event == key,
                UserEventCounter.account_id == workspace_id,
            )
        )
        return int(res.scalar() or 0)

    async def list_locked_achievements(
        self, user_id: UUID, workspace_id: UUID
    ) -> list[Achievement]:
        res = await self._db.execute(
            select(Achievement).where(
                Achievement.account_id == workspace_id,
                ~Achievement.id.in_(
                    select(UserAchievement.achievement_id).where(
                        UserAchievement.user_id == user_id,
                        UserAchievement.account_id == workspace_id,
                    )
                ),
            )
        )
        return list(res.scalars().all())

    async def is_user_premium(self, user_id: UUID) -> bool:
        res = await self._db.execute(select(User.is_premium).where(User.id == user_id))
        return bool(res.scalar())

    async def count_nodes_by_author(self, user_id: UUID, workspace_id: UUID) -> int:
        res = await self._db.execute(
            select(func.count(Node.id)).where(
                Node.author_id == user_id,
                Node.workspace_id == workspace_id,
            )
        )
        return int(res.scalar() or 0)

    async def sum_views_by_author(self, user_id: UUID, workspace_id: UUID) -> int:
        res = await self._db.execute(
            select(func.coalesce(func.sum(Node.views), 0)).where(
                Node.author_id == user_id,
                Node.workspace_id == workspace_id,
            )
        )
        return int(res.scalar() or 0)

    # CRUD (admin)
    async def list_achievements(self, workspace_id: UUID) -> list[Achievement]:
        res = await self._db.execute(
            select(Achievement)
            .where(Achievement.workspace_id == workspace_id)
            .order_by(Achievement.title.asc())
        )
        return list(res.scalars().all())

    async def exists_code(self, code: str, workspace_id: UUID) -> bool:
        res = await self._db.execute(
            select(Achievement).where(
                Achievement.code == code,
                Achievement.workspace_id == workspace_id,
            )
        )
        return res.scalars().first() is not None

    async def create_achievement(
        self, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Achievement:
        item = Achievement(
            workspace_id=workspace_id,
            created_by_user_id=actor_id,
            **data,
        )
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def update_achievement_fields(
        self,
        item: Achievement,
        data: dict[str, Any],
        workspace_id: UUID,
        actor_id: UUID,
    ) -> Achievement:
        if item.workspace_id != workspace_id:
            raise ValueError("workspace_mismatch")
        for k, v in (data or {}).items():
            setattr(item, k, v)
        item.updated_by_user_id = actor_id
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def delete_achievement(self, item: Achievement, workspace_id: UUID) -> None:
        if item.workspace_id != workspace_id:
            raise ValueError("workspace_mismatch")
        await self._db.delete(item)
        await self._db.flush()
