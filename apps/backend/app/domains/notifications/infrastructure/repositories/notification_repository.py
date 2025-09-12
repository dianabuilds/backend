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
from app.domains.notifications.events.models import NotificationCreated
from app.domains.notifications.events.publisher import publish_notification_created


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
        placement: Any,
        is_preview: bool = False,
    ) -> dict[str, Any]:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            placement=placement,
            is_preview=is_preview,
        )
        # Ensure ID is generated before emitting to outbox (same transaction)
        self._db.add(notif)
        await self._db.flush()
        # Emit outbox event within the same transaction for reliability
        await publish_notification_created(
            self._db,
            data=NotificationCreated(
                id=notif.id,
                user_id=notif.user_id,
                title=notif.title,
                message=notif.message,
                created_at=notif.created_at,
                type=notif.type,  # type: ignore[arg-type]
                placement=notif.placement,  # type: ignore[arg-type]
                is_preview=notif.is_preview,
            ),
        )
        await self._db.commit()
        await self._db.refresh(notif)
        data = NotificationOut.model_validate(notif).model_dump()
        return data
