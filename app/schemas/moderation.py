from datetime import datetime

from pydantic import BaseModel


class RestrictionCreate(BaseModel):
    reason: str | None = None
    expires_at: datetime | None = None


class ContentHide(BaseModel):
    reason: str
