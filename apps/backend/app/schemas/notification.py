from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class NotificationType(str, Enum):
    quest = "quest"
    system = "system"
    moderation = "moderation"
    achievement = "achievement"
    purchase = "purchase"


class NotificationPlacement(str, Enum):
    inbox = "inbox"
    banner = "banner"


class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None
    type: NotificationType
    placement: NotificationPlacement = NotificationPlacement.inbox
    is_preview: bool

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: NotificationType = NotificationType.system
    placement: NotificationPlacement = NotificationPlacement.inbox


class NotificationFilter(BaseModel):
    placement: NotificationPlacement | None = None


__all__ = [
    "NotificationType",
    "NotificationPlacement",
    "NotificationOut",
    "NotificationCreate",
    "NotificationFilter",
]
