from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quests.application.access_service import AccessService
from app.domains.quests.application.quest_service import QuestService
from app.domains.quests.infrastructure.notifications_adapter import NotificationsAdapter
from app.domains.quests.infrastructure.repositories.access_repository import (
    AccessRepository,
)
from app.domains.quests.infrastructure.repositories.event_quests_repository import (
    EventQuestsRepository,
)
from app.schemas.notification import NotificationType


async def check_quest_completion(db: AsyncSession, user, node, tenant_id) -> None:
    """
    Совместимая доменная точка входа для проверки завершения и награждения в Event Quests.
    """
    service = QuestService(EventQuestsRepository(db), NotificationsAdapter(db))
    await service.check_quest_completion(
        user=user,
        node=node,
        reward_premium_days=7,
        notification_type=NotificationType.quest,
        tenant_id=tenant_id,
    )


async def has_access(db: AsyncSession, user, quest, tenant_id) -> bool:
    """
    Совместимая доменная точка входа для проверки доступа к квесту.
    """
    service = AccessService(AccessRepository(db))
    return await service.has_access(user=user, quest=quest, tenant_id=tenant_id)
