from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .nodes_common import Status, Visibility, Version

class ContentBase(BaseModel):
    title: str
    slug: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: Status = Status.draft
    visibility: Visibility = Visibility.private


class NodeItem(ContentBase):
    id: UUID
    type: str
    workspace_id: UUID
    version: Version
    cover_media_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
