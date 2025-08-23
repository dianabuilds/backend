from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ContentStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"


class ContentVisibility(str, Enum):
    private = "private"
    unlisted = "unlisted"
    public = "public"


class ContentBase(BaseModel):
    title: str
    slug: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: ContentStatus = ContentStatus.draft
    visibility: ContentVisibility = ContentVisibility.private


class NodeItem(ContentBase):
    id: UUID
    type: str
    workspace_id: UUID
    version: int
    cover_media_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
