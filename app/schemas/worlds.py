from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class WorldTemplateIn(BaseModel):
    title: str
    locale: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class WorldTemplateOut(BaseModel):
    id: UUID
    title: str
    locale: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterIn(BaseModel):
    name: str
    role: Optional[str] = None
    description: Optional[str] = None
    traits: Optional[dict[str, Any]] = None


class CharacterOut(BaseModel):
    id: UUID
    world_id: UUID
    name: str
    role: Optional[str] = None
    description: Optional[str] = None
    traits: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
