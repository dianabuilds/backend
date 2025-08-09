from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationOut
from app.services.notification_ws import manager as ws_manager


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    message: str,
    type: NotificationType = NotificationType.system,
) -> Notification:
    notif = Notification(user_id=user_id, title=title, message=message, type=type)
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    try:
        data = NotificationOut.model_validate(notif).model_dump()
        await ws_manager.send_notification(user_id, data)
    except Exception:
        # If websocket delivery fails, continue without interrupting creation
        pass
    return notif
