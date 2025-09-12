from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest, QuestPurchase
from app.domains.users.infrastructure.models.user import User


async def can_view(db: AsyncSession, *, quest: Quest, user: User) -> bool:
    """Можно ли просматривать квест (в т.ч. стартовать)."""
    if quest.author_id == user.id:
        return True
    if (quest.price is None or quest.price == 0) and not quest.is_premium_only:
        return True
    if quest.is_premium_only and user.is_premium:
        return True
    res = await db.execute(
        select(QuestPurchase).where(
            QuestPurchase.quest_id == quest.id,
            QuestPurchase.user_id == user.id,
            QuestPurchase.tenant_id == quest.tenant_id,
        )
    )
    return res.scalars().first() is not None


async def can_start(db: AsyncSession, *, quest: Quest, user: User) -> bool:
    """Правила для начала прохождения: сейчас совпадает с can_view."""
    return await can_view(db, quest=quest, user=user)
