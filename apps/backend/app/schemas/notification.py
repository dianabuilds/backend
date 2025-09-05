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


class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None
    type: NotificationType
    is_preview: bool

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    workspace_id: UUID | None = None
    user_id: UUID
    title: str
    message: str
    type: NotificationType = NotificationType.system


class NotificationFilter(BaseModel):
    workspace_id: UUID | None = None


__all__ = [
    "NotificationType",
    "NotificationOut",
    "NotificationCreate",
    "NotificationFilter",
]
