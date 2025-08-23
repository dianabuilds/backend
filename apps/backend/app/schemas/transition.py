from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class NodeTransitionType(str, Enum):
    manual = "manual"
    locked = "locked"


class TransitionCondition(BaseModel):
    """Schema for manual transition conditions."""

    premium_required: bool | None = Field(default=None, example=True)
    nft_required: str | None = Field(default=None, example="cool-nft")
    tags: list[str] | None = Field(default=None, example=["tag-a", "tag-b"])
    cooldown: int | None = Field(default=None, ge=0, example=3600)

    model_config = {"extra": "forbid"}


class NodeTransitionCreate(BaseModel):
    to_slug: str
    label: str | None = None
    type: NodeTransitionType = NodeTransitionType.manual
    condition: TransitionCondition | None = Field(
        default_factory=TransitionCondition,
        examples=[{"premium_required": True}],
    )
    weight: int = 1


class NodeTransitionUpdate(BaseModel):
    from_slug: str | None = Field(default=None, example="start")
    to_slug: str | None = Field(default=None, example="end")
    label: str | None = Field(default=None, example="Go next")
    type: NodeTransitionType | None = None
    condition: TransitionCondition | None = Field(
        default=None, example={"premium_required": True}
    )
    weight: int | None = Field(default=None, ge=1, example=1)


class TransitionOption(BaseModel):
    slug: str
    label: str | None = None
    mode: str


class NextTransitions(BaseModel):
    mode: str
    transitions: list[TransitionOption]


class TransitionMode(BaseModel):
    """Describes a transition selection mode."""

    mode: str
    label: str
    filters: dict[str, Any] | None = Field(default_factory=dict)


class TransitionController(BaseModel):
    """DSL definition for transition behaviour."""

    type: Literal["transition_controller"] = "transition_controller"
    max_options: int = 3
    default_mode: str = "auto"
    modes: list[TransitionMode] = Field(default_factory=list)


class AvailableMode(BaseModel):
    mode: str
    label: str


class NextModes(BaseModel):
    default_mode: str
    modes: list[AvailableMode]


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


class AdminTransitionOut(BaseModel):
    id: UUID
    from_slug: str
    to_slug: str
    type: NodeTransitionType
    weight: int
    label: str | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TransitionDisableRequest(BaseModel):
    slug: str = Field(..., example="intro")
