from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domains.notifications.schemas.notification import (
    NotificationPlacement,
    NotificationType,
)


@dataclass(frozen=True)
class NotificationCreated:
    id: UUID
    user_id: UUID
    title: str
    message: str
    created_at: datetime
    type: NotificationType
    placement: NotificationPlacement
    is_preview: bool


__all__ = ["NotificationCreated"]

