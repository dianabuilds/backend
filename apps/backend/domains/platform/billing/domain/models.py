from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Plan:
    id: str
    slug: str
    title: str
    price_cents: int | None
    currency: str | None
    is_active: bool
    order: int
    monthly_limits: dict[str, int] | None
    features: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Subscription:
    id: str
    user_id: str
    plan_id: str
    status: str
    auto_renew: bool
    started_at: datetime
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class LedgerTx:
    id: str
    user_id: str
    gateway_slug: str | None
    product_type: str
    product_id: str | None
    currency: str | None
    gross_cents: int
    fee_cents: int
    net_cents: int
    status: str
    created_at: datetime
    meta: dict[str, Any] | None


__all__ = ["Plan", "Subscription", "LedgerTx"]
