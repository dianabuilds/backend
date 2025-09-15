from __future__ import annotations

from pydantic import BaseModel, Field


class QuotaConsumeIn(BaseModel):
    user_id: str = Field(min_length=1)
    key: str = Field(min_length=1)
    limit: int = Field(ge=0)
    amount: int = Field(default=1, ge=1)
    scope: str = Field(default="day", pattern="^(day|month)$")


class QuotaConsumeOut(BaseModel):
    allowed: bool
    remaining: int
    limit: int
    scope: str
    reset_at: str | None
    overage: bool


__all__ = ["QuotaConsumeIn", "QuotaConsumeOut"]
