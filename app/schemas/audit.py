from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime
    extra: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
