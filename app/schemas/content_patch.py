from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ContentPatchCreate(BaseModel):
    content_id: UUID
    data: dict[str, object]


class ContentPatchOut(BaseModel):
    id: UUID
    content_id: UUID
    data: dict[str, object]
    created_at: datetime
    reverted_at: datetime | None = None

    class Config:
        orm_mode = True
