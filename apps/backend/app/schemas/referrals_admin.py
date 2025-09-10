from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReferralCodeAdminOut(BaseModel):
    id: UUID
    owner_user_id: UUID | None = None
    code: str
    uses_count: int
    active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReferralEventAdminOut(BaseModel):
    id: UUID
    code_id: UUID | None = None
    code: str | None = None
    referrer_user_id: UUID | None = None
    referee_user_id: UUID
    event_type: str
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivateCodeOut(BaseModel):
    ok: bool = True
    code: str


class DeactivateCodeOut(BaseModel):
    ok: bool = True
