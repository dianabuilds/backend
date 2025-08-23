from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class NotificationType(str, Enum):
    quest = "quest"
    system = "system"
    moderation = "moderation"


class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None
    type: NotificationType

    model_config = {"from_attributes": True}
