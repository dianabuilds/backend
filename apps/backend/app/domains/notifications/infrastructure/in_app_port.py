from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.application.ports.notifications import INotificationPort
from app.domains.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)


class InAppNotificationPort(INotificationPort):
    """Notification port delivering messages via in-app channel."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._svc = NotifyService(NotificationRepository(db), WebsocketPusher(ws_manager))

    async def notify(
        self,
        trigger: str,
        user_id: UUID,
        *,
        workspace_id: UUID | None = None,
        title: str,
        message: str,
        preview: PreviewContext | None = None,
    ) -> None:
        if workspace_id is None:
            return
        await self._svc.create_notification(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            message=message,
            type=None,
            preview=preview,
        )


__all__ = ["InAppNotificationPort"]
