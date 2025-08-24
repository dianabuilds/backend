from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator


class NodePatchCreate(BaseModel):
    node_id: UUID
    data: dict[str, object]


class NodePatchOut(BaseModel):
    id: UUID
    node_id: UUID
    data: dict[str, object]
    quest_data: dict[str, object] | None = None
    created_at: datetime
    reverted_at: datetime | None = None

    class Config:
        orm_mode = True

    @model_validator(mode="after")
    def _extract_quest_data(self) -> NodePatchOut:
        if self.quest_data is None and isinstance(self.data, dict):
            quest_part = self.data.get("quest_data")
            if isinstance(quest_part, dict):
                self.quest_data = quest_part
        return self


class NodePatchDiffOut(NodePatchOut):
    diff: str | None = None
