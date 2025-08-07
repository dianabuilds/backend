from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NodeTransitionType(str, Enum):
    manual = "manual"
    locked = "locked"


class NodeTransitionCreate(BaseModel):
    to_slug: str
    label: str | None = None
    type: NodeTransitionType = NodeTransitionType.manual
    condition: dict[str, Any] | None = Field(default_factory=dict)
    weight: int = 1


class TransitionOption(BaseModel):
    slug: str
    label: str | None = None
    mode: str


class NextTransitions(BaseModel):
    mode: str
    transitions: list[TransitionOption]


class NodeTransitionOut(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    type: NodeTransitionType
    condition: dict[str, Any]
    weight: int
    label: str | None
    created_by: UUID

    model_config = {"from_attributes": True}
