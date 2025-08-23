from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.application.ports.notification_repo import INotificationRepository
from app.domains.notifications.infrastructure.models.notification_models import Notification
from app.schemas.notification import NotificationOut


class NotificationRepository(INotificationRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_and_commit(
        self,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
    ) -> Dict[str, Any]:
        notif = Notification(user_id=user_id, title=title, message=message, type=type)
        self._db.add(notif)
        await self._db.commit()
        await self._db.refresh(notif)
        data = NotificationOut.model_validate(notif).model_dump()
        return data
