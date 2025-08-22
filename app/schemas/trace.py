from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.navigation.infrastructure.models.transition_models import NodeTraceKind, NodeTraceVisibility


class TraceUser(BaseModel):
    id: UUID
    username: str | None = None

    model_config = {"from_attributes": True}


class NodeTraceCreate(BaseModel):
    node_id: UUID
    kind: NodeTraceKind
    comment: str | None = None
    tags: list[str] = Field(default_factory=list)
    visibility: NodeTraceVisibility = NodeTraceVisibility.public


class NodeTraceOut(BaseModel):
    id: UUID
    created_at: datetime
    user: TraceUser | None = None
    kind: NodeTraceKind
    comment: str | None = None
    tags: list[str] = Field(default_factory=list)
    visibility: NodeTraceVisibility

    model_config = {"from_attributes": True}
