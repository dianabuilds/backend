from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class QuestBase(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    tags: list[str] = []
    price: Optional[int] = None
    is_premium_only: bool = False
    entry_node_id: Optional[UUID] = None
    nodes: list[UUID] = []
    custom_transitions: Optional[dict] = None
    allow_comments: bool = True
    # generation meta
    structure: Optional[str] = None
    length: Optional[str] = None
    tone: Optional[str] = None
    genre: Optional[str] = None
    locale: Optional[str] = None
    cost_generation: Optional[int] = None


class QuestCreate(QuestBase):
    title: str


class QuestUpdate(QuestBase):
    pass


class QuestOut(QuestBase):
    id: UUID
    slug: str
    author_id: UUID
    is_draft: bool
    published_at: Optional[datetime]
    created_at: datetime
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None

    class Config:
        orm_mode = True


class QuestProgressOut(BaseModel):
    current_node_id: UUID
    started_at: datetime

    class Config:
        orm_mode = True


class QuestBuyIn(BaseModel):
    payment_token: str | None = None
