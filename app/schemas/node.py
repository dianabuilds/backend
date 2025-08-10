from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from typing import Literal


class ContentFormat(str, Enum):
    text = "text"
    markdown = "markdown"
    rich_json = "rich_json"
    html = "html"
    image_set = "image_set"


class NodeBase(BaseModel):
    title: str | None = None
    content_format: ContentFormat
    content: Any
    media: list[str] | None = None
    tags: list[str] | None = None
    is_public: bool = False
    meta: dict = Field(default_factory=dict)
    premium_only: bool | None = None
    nft_required: str | None = None
    ai_generated: bool | None = None
    allow_feedback: bool = True
    is_recommendable: bool = True


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    title: str | None = None
    content: Any | None = None
    media: list[str] | None = None
    tags: list[str] | None = None
    is_public: bool | None = None
    allow_feedback: bool | None = None
    is_recommendable: bool | None = None
    premium_only: bool | None = None
    nft_required: str | None = None
    ai_generated: bool | None = None


class NodeOut(NodeBase):
    tags: list[str] = Field(default_factory=list, validation_alias="tag_slugs")
    id: UUID
    slug: str
    author_id: UUID
    views: int
    reactions: dict[str, int]
    created_at: datetime
    updated_at: datetime
    is_visible: bool
    popularity_score: float

    model_config = {"from_attributes": True}


class ReactionUpdate(BaseModel):
    reaction: str
    action: Literal["add", "remove"]


class NodeBulkOperation(BaseModel):
    """Payload for bulk node admin operations."""

    ids: list[UUID]
    op: Literal[
        "hide",
        "show",
        "public",
        "private",
        "toggle_premium",
        "toggle_recommendable",
    ]
