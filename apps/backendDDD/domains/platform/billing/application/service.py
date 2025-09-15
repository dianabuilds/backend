from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.backendDDD.domains.platform.billing.domain.models import Plan
from apps.backendDDD.domains.platform.billing.ports import (
    CheckoutResult,
    LedgerRepo,
    PaymentProvider,
    PlanRepo,
    SubscriptionRepo,
)


@dataclass
class BillingService:
    plans: PlanRepo
    subs: SubscriptionRepo
    ledger: LedgerRepo
    provider: PaymentProvider

    async def list_plans(self) -> list[Plan]:
        return await self.plans.list_active()

    async def checkout(self, user_id: str, plan_slug: str) -> CheckoutResult:
        plan = await self.plans.get_by_slug(plan_slug)
        if not plan:
            raise ValueError("plan_not_found")
        return await self.provider.checkout(user_id, plan)

    async def handle_webhook(
        self, payload: bytes, signature: str | None
    ) -> dict[str, Any]:
        ok = await self.provider.verify_webhook(payload, signature)
        if not ok:
            return {"ok": False}
        # For mock provider, accept and do nothing else
        return {"ok": True}

    async def get_subscription_for_user(self, user_id: str) -> dict[str, Any] | None:
        sub = await self.subs.get_active_for_user(user_id)
        return None if not sub else sub.__dict__


__all__ = ["BillingService"]
