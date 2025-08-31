import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator


class AuditLogOut(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    workspace_id: UUID | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime
    extra: dict[str, Any] | None = None

    @field_validator("before", "after", "extra", mode="before")
    @classmethod
    def _load_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    model_config = {"from_attributes": True}
