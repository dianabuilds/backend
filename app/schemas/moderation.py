from datetime import datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel


class RestrictionCreate(BaseModel):
    reason: str | None = None
    expires_at: datetime | None = None


class RestrictionAdminCreate(BaseModel):
    user_id: UUID
    type: Literal["ban", "post_restrict"]
    reason: str | None = None
    expires_at: datetime | None = None


class RestrictionAdminUpdate(BaseModel):
    reason: str | None = None
    expires_at: datetime | None = None


class ContentHide(BaseModel):
    reason: str


class HiddenNodeOut(BaseModel):
    slug: str
    title: str | None = None
    reason: str | None = None
    hidden_by: UUID | None = None
    hidden_at: datetime


class RestrictionOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    reason: str | None = None
    created_at: datetime
    expires_at: datetime | None = None
    issued_by: UUID | None = None

    model_config = {
        "from_attributes": True,
    }
