from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.billing.domain.models import Plan
from domains.platform.billing.ports import (
    BillingHistoryRepo,
    BillingSummaryRepo,
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
    summary_repo: BillingSummaryRepo
    history_repo: BillingHistoryRepo

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

    async def get_summary_for_user(self, user_id: str) -> dict[str, Any]:
        summary = await self.summary_repo.get_summary(user_id)
        return {
            "plan": summary.plan,
            "subscription": summary.subscription,
            "payment": {
                "mode": "evm_wallet",
                "title": "EVM wallet",
                "message": "Currently we only support EVM (SIWE) wallets. Card payments are coming soon.",
                "coming_soon": True,
            },
        }

    async def get_history_for_user(
        self, user_id: str, limit: int = 20
    ) -> dict[str, Any]:
        safe_limit = int(max(1, min(limit, 100)))
        history = await self.history_repo.get_history(user_id, limit=safe_limit)
        return {"items": history.items, "coming_soon": history.coming_soon}


__all__ = ["BillingService"]
