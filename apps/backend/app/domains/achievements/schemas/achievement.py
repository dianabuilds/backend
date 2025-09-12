from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AchievementOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    unlocked: bool
    unlocked_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

__all__ = ["AchievementOut"]

