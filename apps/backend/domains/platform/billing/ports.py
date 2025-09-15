from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from domains.platform.billing.domain.models import Plan, Subscription


@dataclass
class CheckoutResult:
    url: str | None
    provider: str
    external_id: str


class PaymentProvider(Protocol):
    async def checkout(self, user_id: str, plan: Plan) -> CheckoutResult: ...
    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool: ...


class PlanRepo(Protocol):
    async def list_active(self) -> list[Plan]: ...
    async def get_by_slug(self, slug: str) -> Plan | None: ...
    async def upsert(self, p: dict[str, Any]) -> Plan: ...
    async def delete(self, plan_id: str) -> None: ...


class SubscriptionRepo(Protocol):
    async def get_active_for_user(self, user_id: str) -> Subscription | None: ...
    async def activate(
        self, user_id: str, plan_id: str, auto_renew: bool, ends_at: str | None = None
    ) -> Subscription: ...


class LedgerRepo(Protocol):
    async def add_tx(self, tx: dict[str, Any]) -> None: ...


__all__ = [
    "PaymentProvider",
    "CheckoutResult",
    "PlanRepo",
    "SubscriptionRepo",
    "LedgerRepo",
]
