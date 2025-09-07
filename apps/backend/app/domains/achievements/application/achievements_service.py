from __future__ import annotations

import builtins
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.achievements.application.ports.repository import (
    IAchievementsRepository,
)
from app.domains.achievements.infrastructure.models.achievement_models import (
    Achievement,
    UserAchievement,
)
from app.domains.system.events import AchievementUnlocked, get_event_bus
from app.models.event_counter import UserEventCounter


class AchievementsService:
    """Domain service for managing achievements."""

    def __init__(self, repo: IAchievementsRepository) -> None:
        self._repo = repo

    async def list(
        self, workspace_id: UUID, user_id: UUID
    ) -> list[tuple[Achievement, UserAchievement | None]]:
        """Return all achievements with optional unlock info for user."""
        return await self._repo.list_user_achievements(user_id, workspace_id)

    async def grant_manual(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        achievement_id: UUID,
    ) -> bool:
        if await self._repo.user_has_achievement(user_id, achievement_id, workspace_id):
            return False
        ach = await self._repo.get_achievement(achievement_id, workspace_id)
        if not ach:
            return False
        await self._repo.add_user_achievement(user_id, achievement_id, workspace_id)
        await get_event_bus().publish(
            AchievementUnlocked(
                achievement_id=achievement_id,
                user_id=user_id,
                workspace_id=workspace_id,
                title=ach.title,
                message=ach.title,
            )
        )
        await db.commit()
        return True

    async def revoke_manual(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        achievement_id: UUID,
    ) -> bool:
        ach = await self._repo.get_achievement(achievement_id, workspace_id)
        if not ach:
            return False
        ok = await self._repo.delete_user_achievement(user_id, achievement_id, workspace_id)
        if ok:
            await db.commit()
        return ok

    @staticmethod
    async def process_event(
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        event: str,
        payload: dict[str, Any] | None = None,
        preview: PreviewContext | None = None,
    ) -> builtins.list[Achievement]:
        """Handle user event and unlock achievements if conditions met."""

        payload = payload or {}

        dry_run = preview and preview.mode == "dry_run"

        counter = await db.get(
            UserEventCounter,
            {"account_id": workspace_id, "user_id": user_id, "event": event},
        )
        current_count = int(counter.count or 0) if counter else 0
        new_count = current_count + 1
        if not dry_run:
            if not counter:
                counter = UserEventCounter(
                    account_id=workspace_id, user_id=user_id, event=event, count=0
                )
                db.add(counter)
                await db.flush()
            counter.count = new_count
            await db.flush()

        res = await db.execute(select(Achievement).where(Achievement.workspace_id == workspace_id))
        all_achs: list[Achievement] = list(res.scalars().all())

        def _match_condition(ach: Achievement) -> bool:
            cond = ach.condition or {}
            ctype = cond.get("type")
            if ctype == "event_count":
                ev = cond.get("event")
                cnt = int(cond.get("count") or 0)
                return ev == event and (counter.count or 0) >= cnt
            if ctype == "nodes_created":
                cnt = int(cond.get("count") or 0)
                return event == "node_created" and (counter.count or 0) >= cnt
            return False

        candidates = [a for a in all_achs if _match_condition(a)]
        if not candidates:
            if not dry_run:
                await db.commit()
            return []

        unlocked: list[Achievement] = []
        for ach in candidates:
            exists = await db.execute(
                select(UserAchievement).where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == ach.id,
                    UserAchievement.workspace_id == workspace_id,
                )
            )
            if exists.scalars().first():
                continue
            if dry_run:
                unlocked.append(ach)
                continue
            ua = UserAchievement(
                user_id=user_id,
                achievement_id=ach.id,
                workspace_id=workspace_id,
                unlocked_at=datetime.utcnow(),
            )
            db.add(ua)
            await get_event_bus().publish(
                AchievementUnlocked(
                    achievement_id=ach.id,
                    user_id=user_id,
                    workspace_id=workspace_id,
                    title=ach.title or ach.code,
                    message=ach.title or ach.code,
                )
            )
            unlocked.append(ach)

        if not dry_run:
            await db.commit()
        return unlocked


__all__ = ["AchievementsService"]
