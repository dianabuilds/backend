from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.models.node import Node
from app.models.event_counter import UserEventCounter
from app.services.notifications import create_notification


class AchievementsService:

    @classmethod
    async def grant_manual(
        cls, db: AsyncSession, user_id: UUID, achievement_id: UUID
    ) -> bool:
        """Grant an achievement to a user manually.

        Returns True if a new record was created, False if the user already had it.
        """
        result = await db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        if result.scalars().first():
            return False

        ach = await db.get(Achievement, achievement_id)
        if not ach:
            return False

        db.add(UserAchievement(user_id=user_id, achievement_id=achievement_id))
        await create_notification(
            db=db,
            user_id=user_id,
            title="Achievement unlocked",
            message=ach.title,
        )
        await db.commit()
        return True

    @classmethod
    async def revoke_manual(
        cls, db: AsyncSession, user_id: UUID, achievement_id: UUID
    ) -> bool:
        """Revoke an achievement from a user."""
        result = await db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        ua = result.scalars().first()
        if not ua:
            return False
        await db.delete(ua)
        await db.commit()
        return True

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
        await cls._increment_counter(db, user_id, key)

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
            count = await cls._get_counter(db, user_id, event_type)
            return count >= int(condition.get("count", 0))
        if ctype == "tag_interaction":
            if event_type != "tag_interaction" or metadata.get("tag") != condition.get("tag"):
                return False
            key = f"tag:{condition.get('tag')}"
            count = await cls._get_counter(db, user_id, key)
            return count >= int(condition.get("count", 0))
        if ctype == "premium_status":
            result = await db.execute(
                select(User.is_premium).where(User.id == user_id)
            )
            return bool(result.scalar()) == bool(condition.get("value"))
        if ctype == "first_action":
            if event_type != condition.get("event"):
                return False
            count = await cls._get_counter(db, user_id, event_type)
            return count == 1
        if ctype == "quest_complete":
            if event_type != "quest_complete":
                return False
            return metadata.get("quest_id") == condition.get("quest_id")
        if ctype == "nodes_created":
            result = await db.execute(
                select(func.count(Node.id)).where(Node.author_id == user_id)
            )
            count = result.scalar() or 0
            return count >= int(condition.get("count", 0))
        if ctype == "views_count":
            result = await db.execute(
                select(func.coalesce(func.sum(Node.views), 0)).where(Node.author_id == user_id)
            )
            views = result.scalar() or 0
            return views >= int(condition.get("count", 0))
        return False

    @staticmethod
    async def _increment_counter(db: AsyncSession, user_id: UUID, key: str) -> None:
        result = await db.execute(
            select(UserEventCounter).where(
                UserEventCounter.user_id == user_id,
                UserEventCounter.event == key,
            )
        )
        counter = result.scalars().first()
        if counter:
            counter.count += 1
        else:
            db.add(UserEventCounter(user_id=user_id, event=key, count=1))

    @staticmethod
    async def _get_counter(db: AsyncSession, user_id: UUID, key: str) -> int:
        result = await db.execute(
            select(UserEventCounter.count).where(
                UserEventCounter.user_id == user_id,
                UserEventCounter.event == key,
            )
        )
        return result.scalar() or 0
