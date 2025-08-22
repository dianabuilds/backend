from __future__ import annotations

from app.domains.quests.application.ports.access_port import IAccessRepository


class AccessService:
    def __init__(self, repo: IAccessRepository) -> None:
        self._repo = repo

    async def has_access(self, *, user, quest) -> bool:
        if quest.author_id == user.id:
            return True
        if (quest.price is None or quest.price == 0) and not quest.is_premium_only:
            return True
        if quest.is_premium_only and user.is_premium:
            return True
        if await self._repo.has_purchase(quest_id=quest.id, user_id=user.id):
            return True
        return False
