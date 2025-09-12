from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .models import NotificationCreated


async def publish_notification_created(db: AsyncSession, *, data: NotificationCreated) -> None:
    payload: dict[str, Any] = {
        "id": str(data.id),
        "user_id": str(data.user_id),
        "title": data.title,
        "message": data.message,
        "created_at": data.created_at.isoformat(),
        "type": data.type,
        "placement": data.placement,
        "is_preview": data.is_preview,
    }
    # Deduplicate by notification id to avoid double sends on retries.
    from app.domains.system.platform.outbox import emit as outbox_emit
    await outbox_emit(
        db,
        topic="event.notification.created.v1",
        payload=payload,
        tenant_id=None,
        dedup_key=f"notification:{payload['id']}",
    )


__all__ = ["publish_notification_created"]
