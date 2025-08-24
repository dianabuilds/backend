from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domains.notifications.application.ports.notification_repo import INotificationRepository
from app.domains.notifications.application.ports.pusher import INotificationPusher


class NotifyService:
    def __init__(self, repo: INotificationRepository, pusher: INotificationPusher) -> None:
        self._repo = repo
        self._pusher = pusher

    async def create_notification(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
    ) -> Dict[str, Any]:
        # Репозиторий создаёт запись и коммитит (сохранено поведение старой реализации)
        dto = await self._repo.create_and_commit(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )
        # Пушим клиенту; сбои доставки не прерывают создание
        try:
            await self._pusher.send(user_id, dto)
        except Exception:
            pass
        return dto
