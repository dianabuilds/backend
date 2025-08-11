from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PremiumPurchaseIn(BaseModel):
    payment_token: str
    days: int = Field(30, gt=0)


class AdminPaymentOut(BaseModel):
    id: UUID
    user_id: UUID
    source: str
    days: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminPremiumGrant(BaseModel):
    days: int = Field(0, ge=0)
