from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class FeatureFlagAudience(str, Enum):
    all = "all"
    premium = "premium"
    beta = "beta"


class FeatureFlagOut(BaseModel):
    key: str
    value: bool
    audience: FeatureFlagAudience = FeatureFlagAudience.all
    description: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None

    model_config = {"from_attributes": True}


class FeatureFlagUpdateIn(BaseModel):
    value: bool | None = None
    description: str | None = None
    audience: FeatureFlagAudience | None = None
