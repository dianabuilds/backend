from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.node import (
    NodeBulkOperation,
    NodeBulkPatch,
    NodeCreate,
    NodeOut,
    NodeUpdate,
)
from app.schemas.nodes_common import Status


class AdminNodeOut(BaseModel):
    """Detailed node payload used by the admin UI."""

    id: int
    content_id: int = Field(alias="contentId")
    node_id: int = Field(alias="nodeId")
    workspace_id: UUID = Field(alias="workspaceId")
    node_type: str = Field(alias="nodeType")
    type: str | None = None
    slug: str
    title: str | None = None
    summary: str | None = None
    status: Status
    meta: dict = Field(default_factory=dict)
    content: dict | list | None = None
    coverUrl: str | None = None
    media: list[str] = Field(default_factory=list)
    is_public: bool = Field(alias="isPublic")
    is_visible: bool = Field(default=True, alias="isVisible")
    allow_feedback: bool = Field(default=True, alias="allowFeedback")
    is_recommendable: bool = Field(default=True, alias="isRecommendable")
    premium_only: bool | None = Field(default=None, alias="premiumOnly")
    nft_required: str | None = Field(default=None, alias="nftRequired")
    ai_generated: bool | None = Field(default=None, alias="aiGenerated")
    author_id: UUID | None = Field(default=None, alias="authorId")
    created_by_user_id: UUID | None = Field(default=None, alias="createdByUserId")
    updated_by_user_id: UUID | None = Field(default=None, alias="updatedByUserId")
    views: int = 0
    reactions: dict = Field(default_factory=dict)
    popularity_score: float = Field(default=0.0, alias="popularityScore")
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class AdminNodeList(BaseModel):
    items: list[AdminNodeOut]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


__all__ = [
    "NodeCreate",
    "NodeUpdate",
    "NodeOut",
    "AdminNodeOut",
    "AdminNodeList",
    "NodeBulkOperation",
    "NodeBulkPatch",
]
