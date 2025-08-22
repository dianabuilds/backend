from __future__ import annotations

from typing import Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.achievements.application.ports.notifications_port import INotificationPort
from app.domains.achievements.application.ports.repository import IAchievementsRepository
from app.domains.achievements.infrastructure.models.achievement_models import Achievement


class AchievementsService:
    def __init__(self, repo: IAchievementsRepository, notifier: INotificationPort) -> None:
        self._repo = repo
        self._notifier = notifier
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.achievements.infrastructure.models.achievement_models import Achievement, UserAchievement
from app.domains.notifications.infrastructure.models.notification_models import Notification
from app.models.event_counter import UserEventCounter


class AchievementsService:
    @staticmethod
    async def process_event(
        db: AsyncSession,
        user_id: UUID,
        event: str,
        payload: Dict[str, Any] | None = None,
    ) -> List[Achievement]:
        """
        Обрабатывает событие пользователя:
        - инкрементирует счетчик UserEventCounter(user_id, event)
        - находит достижения с condition.type == 'event_count' и совпадающим event,
          порог которых выполнен
        - создает UserAchievement и Notification для новых достижений
        Возвращает список разблокированных достижений (Achievement).
        """
        # 1) Инкрементируем счетчик события
        counter = await db.get(UserEventCounter, {"user_id": user_id, "event": event})
        if not counter:
            counter = UserEventCounter(user_id=user_id, event=event, count=0)
            db.add(counter)
            # flush чтобы первичный ключ (композитный) был в сессии
            await db.flush()
        counter.count = int(counter.count or 0) + 1
        await db.flush()

        # 2) Загружаем все достижения (фильтрация в памяти — достаточно для тестов/админов)
        res = await db.execute(select(Achievement))
        all_achs: list[Achievement] = list(res.scalars().all())

        # 3) Отбираем подходящие по условию (event_count)
        def _match_condition(ach: Achievement) -> bool:
            cond = ach.condition or {}
            ctype = cond.get("type")
            if ctype == "event_count":
                # условие: счетчик по заданному событию >= count
                ev = cond.get("event")
                cnt = int(cond.get("count") or 0)
                return ev == event and (counter.count or 0) >= cnt
            if ctype == "nodes_created":
                # совместимость: интерпретируем как event_count по "node_created"
                cnt = int(cond.get("count") or 0)
                return event == "node_created" and (counter.count or 0) >= cnt
            return False

        candidates = [a for a in all_achs if _match_condition(a)]
        if not candidates:
            await db.commit()
            return []

        # 4) Исключаем уже разблокированные пользователем
        unlocked: list[Achievement] = []
        for ach in candidates:
            exists = await db.execute(
                select(UserAchievement).where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == ach.id,
                )
            )
            if exists.scalars().first():
                continue
            ua = UserAchievement(user_id=user_id, achievement_id=ach.id, unlocked_at=datetime.utcnow())
            db.add(ua)
            # 5) Создаем уведомление (минимальное)
            note = Notification(
                user_id=user_id,
                message=ach.title or ach.code,
                type="achievement",
                meta={"code": ach.code},
            )
            db.add(note)
            unlocked.append(ach)

        await db.commit()
        return unlocked
    async def grant_manual(self, db: AsyncSession, user_id: UUID, achievement_id: UUID) -> bool:
        if await self._repo.user_has_achievement(user_id, achievement_id):
            return False
        ach = await self._repo.get_achievement(achievement_id)
        if not ach:
            return False
        await self._repo.add_user_achievement(user_id, achievement_id)
        await self._notifier.notify(user_id, title="Achievement unlocked", message=ach.title)
        await db.commit()
        return True

    async def revoke_manual(self, db: AsyncSession, user_id: UUID, achievement_id: UUID) -> bool:
        ok = await self._repo.delete_user_achievement(user_id, achievement_id)
        if ok:
            await db.commit()
        return ok

    async def process_event(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> List[Achievement]:
        metadata = metadata or {}
        key = event_type
        if event_type == "tag_interaction" and metadata.get("tag"):
            key = f"tag:{metadata['tag']}"
        await self._repo.increment_counter(user_id, key)

        achievements = await self._repo.list_locked_achievements(user_id)
        unlocked: List[Achievement] = []
        for ach in achievements:
            if await self._check_condition(ach, user_id, event_type, metadata):
                await self._repo.add_user_achievement(user_id, ach.id)
                await self._notifier.notify(user_id, title="Achievement unlocked", message=ach.title)
                unlocked.append(ach)
        return unlocked

    async def _check_condition(
        self,
        ach: Achievement,
        user_id: UUID,
        event_type: str,
        metadata: dict[str, Any],
    ) -> bool:
        condition: dict[str, Any] = ach.condition or {}
        ctype = condition.get("type")
        if ctype == "event_count":
            if event_type != condition.get("event"):
                return False
            count = await self._repo.get_counter(user_id, event_type)
            return count >= int(condition.get("count", 0))
        if ctype == "tag_interaction":
            if event_type != "tag_interaction" or metadata.get("tag") != condition.get("tag"):
                return False
            key = f"tag:{condition.get('tag')}"
            count = await self._repo.get_counter(user_id, key)
            return count >= int(condition.get("count", 0))
        if ctype == "premium_status":
            return (await self._repo.is_user_premium(user_id)) == bool(condition.get("value"))
        if ctype == "first_action":
            if event_type != condition.get("event"):
                return False
            count = await self._repo.get_counter(user_id, event_type)
            return count == 1
        if ctype == "quest_complete":
            if event_type != "quest_complete":
                return False
            return metadata.get("quest_id") == condition.get("quest_id")
        if ctype == "nodes_created":
            count = await self._repo.count_nodes_by_author(user_id)
            return count >= int(condition.get("count", 0))
        if ctype == "views_count":
            views = await self._repo.sum_views_by_author(user_id)
            return views >= int(condition.get("count", 0))
        return False
