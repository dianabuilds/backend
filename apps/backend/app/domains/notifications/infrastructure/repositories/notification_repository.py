from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.application.ports.notification_repo import (
    INotificationRepository,
)
from app.domains.notifications.infrastructure.models.notification_models import (
    Notification,
)
from app.schemas.notification import NotificationOut


class NotificationRepository(INotificationRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_and_commit(
        self,
        *,
        account_id: UUID | None = None,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
        placement: Any,
        is_preview: bool = False,
    ) -> dict[str, Any]:
        notif = Notification(
            workspace_id=account_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            placement=placement,
            is_preview=is_preview,
        )
        self._db.add(notif)
        await self._db.commit()
        await self._db.refresh(notif)
        data = NotificationOut.model_validate(notif).model_dump()
        return data
