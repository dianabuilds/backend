from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class WorldTemplateIn(BaseModel):
    title: str
    locale: str | None = None
    description: str | None = None
    meta: dict[str, Any] | None = None


class WorldTemplateOut(BaseModel):
    id: UUID
    title: str
    locale: str | None = None
    description: str | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None

    model_config = {"from_attributes": True}


class CharacterIn(BaseModel):
    name: str
    role: str | None = None
    description: str | None = None
    traits: dict[str, Any] | None = None


class CharacterOut(BaseModel):
    id: UUID
    world_id: UUID
    name: str
    role: str | None = None
    description: str | None = None
    traits: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None

    model_config = {"from_attributes": True}
