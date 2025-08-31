from __future__ import annotations

from datetime import datetime

from app.domains.quests.application.ports.event_quests_port import (
    IEventQuestsRepository,
)
from app.domains.quests.application.ports.notifications_port import INotificationPort


class QuestService:
    def __init__(
        self, repo: IEventQuestsRepository, notifier: INotificationPort
    ) -> None:
        self._repo = repo
        self._notifier = notifier

    async def check_quest_completion(
        self,
        *,
        user,
        node,
        reward_premium_days: int,
        notification_type,
        workspace_id,
    ) -> None:
        now = datetime.utcnow()
        quests = await self._repo.get_active_for_node(workspace_id, now, node.id)
        if not quests:
            return
        for quest in quests:
            already = await self._repo.has_completion(quest.id, user.id, workspace_id)
            if already:
                continue
            await self._repo.create_completion(quest.id, user.id, node.id, workspace_id)
            count = await self._repo.count_completions(quest.id, workspace_id)
            if count <= quest.max_rewards:
                # Премиум награда
                try:
                    # Обновление премиума производится в access репозитории, но для простоты MVP делаем в API уровне (совместимость)
                    pass
                except Exception:
                    pass
                await self._notifier.create_notification(
                    user.id,
                    workspace_id=workspace_id,
                    title=f"Quest completed: {quest.title}",
                    message="You were among the first to finish the quest!",
                    type=notification_type,
                )
            else:
                await self._notifier.create_notification(
                    user.id,
                    workspace_id=workspace_id,
                    title=f"Quest completed: {quest.title}",
                    message="Quest completed, but rewards are exhausted.",
                    type=notification_type,
                )
