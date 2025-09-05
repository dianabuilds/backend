from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.quests.application.ports.notifications_port import INotificationPort


class NotificationsAdapter(INotificationPort):
    def __init__(self, db: AsyncSession) -> None:
        self._service = NotifyService(
            NotificationRepository(db), WebsocketPusher(ws_manager)
        )

    async def create_notification(
        self,
        user_id: UUID,
        *,
        workspace_id: UUID | None = None,
        title: str,
        message: str,
        type: Any,
    ) -> None:
        await self._service.create_notification(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )
