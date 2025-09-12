from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quests.application.ports.access_port import IAccessRepository
from app.domains.quests.infrastructure.models.quest_models import QuestPurchase
from app.domains.users.infrastructure.models.user import User


class AccessRepository(IAccessRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def has_purchase(self, *, quest_id, user_id, tenant_id) -> bool:
        res = await self._db.execute(
            select(QuestPurchase).where(
                QuestPurchase.quest_id == quest_id,
                QuestPurchase.user_id == user_id,
                QuestPurchase.tenant_id == tenant_id,
            )
        )
        return res.scalars().first() is not None

    async def grant_premium_days(self, *, user: User, days: int) -> None:
        now = datetime.utcnow()
        user.is_premium = True
        user.premium_until = (user.premium_until or now) + timedelta(days=int(days))
        await self._db.commit()
