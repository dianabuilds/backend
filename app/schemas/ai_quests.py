from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class GenerateQuestIn(BaseModel):
    world_template_id: Optional[UUID] = None
    structure: str  # linear | vn_branching | epic
    length: str     # short | long
    tone: str       # light | dark | ironic | custom
    genre: str
    locale: Optional[str] = None
    extras: dict[str, Any] | None = None


class GenerationJobOut(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_by: UUID | None = None
    provider: str | None = None
    model: str | None = None
    params: dict[str, Any]
    result_quest_id: UUID | None = None
    result_version_id: UUID | None = None
    cost: float | None = None
    token_usage: dict[str, Any] | None = None
    reused: bool = False
    progress: int = 0
    logs: list[str] | None = None
    error: str | None = None

    model_config = {"from_attributes": True}


class TickIn(BaseModel):
    delta: int = 10
    message: str | None = None


class GenerationEnqueued(BaseModel):
    job_id: UUID
