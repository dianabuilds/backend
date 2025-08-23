from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AchievementOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    unlocked: bool
    unlocked_at: datetime | None = None

    class Config:
        orm_mode = True
