from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NodePatchCreate(BaseModel):
    node_id: int
    data: dict[str, object]


class NodePatchOut(BaseModel):
    id: int
    node_id: int
    data: dict[str, object]
    created_at: datetime
    reverted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NodePatchDiffOut(NodePatchOut):
    diff: str | None = None

__all__ = ["NodePatchCreate", "NodePatchOut", "NodePatchDiffOut"]

