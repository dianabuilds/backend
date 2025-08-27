from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuestVersionBase(BaseModel):
    number: int
    status: str
    meta: dict | None = None


class QuestVersionOut(QuestVersionBase):
    id: UUID
    quest_id: UUID
    created_at: datetime
    created_by: UUID | None = None
    released_at: datetime | None = None
    released_by: UUID | None = None
    parent_version_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)
