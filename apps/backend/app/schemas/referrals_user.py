from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MyReferralCodeOut(BaseModel):
    code: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class MyReferralStatsOut(BaseModel):
    total_signups: int

    model_config = ConfigDict(from_attributes=True)
