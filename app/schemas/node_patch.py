from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NodePatchCreate(BaseModel):
    node_id: UUID
    data: dict[str, object]


class NodePatchOut(BaseModel):
    id: UUID
    node_id: UUID
    data: dict[str, object]
    created_at: datetime
    reverted_at: datetime | None = None

    class Config:
        orm_mode = True
