from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel


class SubscriptionPlanIn(BaseModel):
    slug: str
    title: str
    description: str | None = None
    price_cents: int | None = None
    currency: str | None = None
    is_active: bool = True
    order: int = 100
    monthly_limits: Dict[str, int] | None = None
    features: Dict[str, Any] | None = None


class SubscriptionPlanOut(SubscriptionPlanIn):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
