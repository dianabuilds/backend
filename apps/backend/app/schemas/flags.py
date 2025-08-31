from datetime import datetime

from pydantic import BaseModel


class FeatureFlagOut(BaseModel):
    key: str
    value: bool
    description: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None

    model_config = {"from_attributes": True}


class FeatureFlagUpdateIn(BaseModel):
    value: bool | None = None
    description: str | None = None
