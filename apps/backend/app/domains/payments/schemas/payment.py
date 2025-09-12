from __future__ import annotations

from pydantic import BaseModel, Field


class PremiumPurchaseIn(BaseModel):
    payment_token: str
    days: int = Field(30, gt=0)

__all__ = ["PremiumPurchaseIn"]

