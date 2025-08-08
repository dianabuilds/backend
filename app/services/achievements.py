from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.services.notifications import create_notification


class AchievementsService:
    _counters: dict[UUID, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @classmethod
    async def process_event(
        cls,
        db: AsyncSession,
        user_id: UUID,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Process an incoming user event and unlock achievements if conditions met."""
        metadata = metadata or {}
        key = event_type
        if event_type == "tag_interaction" and metadata.get("tag"):
            key = f"tag:{metadata['tag']}"
        cls._counters[user_id][key] += 1

        result = await db.execute(
            select(Achievement).where(
                ~Achievement.id.in_(
                    select(UserAchievement.achievement_id).where(
                        UserAchievement.user_id == user_id
                    )
                )
            )
        )
        achievements = result.scalars().all()
        unlocked = []
        for ach in achievements:
            if await cls._check_condition(ach.condition, user_id, event_type, metadata, db):
                ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                db.add(ua)
                await create_notification(
                    db=db,
                    user_id=user_id,
                    title="Achievement unlocked",
                    message=ach.title,
                )
                unlocked.append(ach)
        return unlocked

    @classmethod
    async def _check_condition(
        cls,
        condition: dict[str, Any],
        user_id: UUID,
        event_type: str,
        metadata: dict[str, Any],
        db: AsyncSession,
    ) -> bool:
        ctype = condition.get("type")
        if ctype == "event_count":
            if event_type != condition.get("event"):
                return False
            count = cls._counters[user_id][event_type]
            return count >= int(condition.get("count", 0))
        if ctype == "tag_interaction":
            if event_type != "tag_interaction" or metadata.get("tag") != condition.get("tag"):
                return False
            key = f"tag:{condition.get('tag')}"
            count = cls._counters[user_id][key]
            return count >= int(condition.get("count", 0))
        if ctype == "premium_status":
            result = await db.execute(
                select(User.is_premium).where(User.id == user_id)
            )
            return bool(result.scalar()) == bool(condition.get("value"))
        if ctype == "first_action":
            if event_type != condition.get("event"):
                return False
            count = cls._counters[user_id][event_type]
            return count == 1
        return False
