from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuestBase(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    cover_image: str | None = None
    tags: list[str] = Field(default_factory=list)
    price: int | None = None
    is_premium_only: bool = False
    entry_node_id: UUID | None = None
    nodes: list[UUID] = Field(default_factory=list)
    custom_transitions: dict | None = None
    allow_comments: bool = True
    # generation meta
    structure: str | None = None
    length: str | None = None
    tone: str | None = None
    genre: str | None = None
    locale: str | None = None
    cost_generation: int | None = None


class QuestCreate(QuestBase):
    title: str


class QuestUpdate(QuestBase):
    pass


class QuestOut(QuestBase):
    id: UUID
    slug: str
    author_id: UUID
    is_draft: bool
    published_at: datetime | None
    created_at: datetime
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class QuestProgressOut(BaseModel):
    current_node_id: UUID
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestBuyIn(BaseModel):
    payment_token: str | None = None
