from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


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
    return notif
