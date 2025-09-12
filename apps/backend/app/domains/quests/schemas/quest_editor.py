from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QuestCreateIn(BaseModel):
    key: str | None = None
    title: str
    tags: list[str] | None = None


class VersionSummary(BaseModel):
    id: UUID
    quest_id: UUID
    number: int
    status: str
    created_at: datetime
    released_at: datetime | None = None

    model_config = {"from_attributes": True}


class QuestSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    current_version_id: UUID | None = None
    versions: list[VersionSummary] = Field(default_factory=list)


class GraphNode(BaseModel):
    key: str
    title: str
    type: str = "normal"
    content: dict[str, Any] | None = None
    rewards: dict[str, Any] | None = None


class GraphEdge(BaseModel):
    from_node_key: str
    to_node_key: str
    label: str | None = None
    condition: dict[str, Any] | None = None


class VersionGraph(BaseModel):
    version: VersionSummary
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ValidateResult(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulateIn(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


class SimulateResult(BaseModel):
    steps: list[dict[str, Any]] = Field(default_factory=list)
    rewards: list[dict[str, Any]] = Field(default_factory=list)

