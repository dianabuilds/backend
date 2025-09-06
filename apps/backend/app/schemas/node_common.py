from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .nodes_common import Status, Version, Visibility


class ContentBase(BaseModel):
    title: str
    slug: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: Status = Status.draft
    visibility: Visibility = Visibility.private


class NodeItem(ContentBase):
    id: int
    type: str
    version: Version
    cover_media_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
