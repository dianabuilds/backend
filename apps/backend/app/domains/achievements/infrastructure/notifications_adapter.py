from __future__ import annotations

from uuid import UUID

from app.domains.achievements.application.ports.notifications_port import INotificationPort
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.repositories.notification_repository import NotificationRepository
from app.domains.notifications.infrastructure.transports.websocket import WebsocketPusher, manager as ws_manager
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationsAdapter(INotificationPort):
    def __init__(self, db: AsyncSession) -> None:
        self._svc = NotifyService(NotificationRepository(db), WebsocketPusher(ws_manager))

    async def notify(self, user_id: UUID, *, title: str, message: str) -> None:
        await self._svc.create_notification(user_id=user_id, title=title, message=message, type=None)
