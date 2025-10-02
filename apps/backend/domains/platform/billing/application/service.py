from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from domains.platform.billing.domain.models import Plan
from domains.platform.billing.ports import (
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

    _log = logging.getLogger(__name__)

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
        summary: dict[str, Any] = {
            "plan": None,
            "subscription": None,
            "payment": {
                "mode": "evm_wallet",
                "title": "EVM wallet",
                "message": "Currently we only support EVM (SIWE) wallets. Card payments are coming soon.",
                "coming_soon": True,
            },
        }
        sub = await self.subs.get_active_for_user(user_id)
        if sub:
            summary["subscription"] = {
                "plan_id": sub.plan_id,
                "status": sub.status,
                "auto_renew": sub.auto_renew,
                "started_at": sub.started_at,
                "ends_at": sub.ends_at,
            }
            plan = await self.plans.get_by_id(sub.plan_id)
            if plan:
                summary["plan"] = {
                    "id": plan.id,
                    "slug": plan.slug,
                    "title": plan.title,
                    "price_cents": plan.price_cents,
                    "currency": plan.currency,
                    "features": plan.features,
                }
        return summary

    async def get_history_for_user(
        self, user_id: str, limit: int = 20
    ) -> dict[str, Any]:
        try:
            rows = await self.ledger.list_for_user(user_id, limit=limit)
        except (SQLAlchemyError, RuntimeError, ValueError) as exc:
            self._log.warning(
                "billing_history_unavailable", extra={"user_id": user_id}, exc_info=exc
            )
            return {"items": [], "coming_soon": True}
        items: list[dict[str, Any]] = []
        for row in rows:
            gross = row.get("gross_cents")
            amount = float(gross) / 100.0 if isinstance(gross, (int, float)) else None
            items.append(
                {
                    "id": row.get("id"),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                    "amount": amount,
                    "currency": row.get("currency"),
                    "provider": row.get("gateway_slug"),
                    "product_type": row.get("product_type"),
                    "meta": row.get("meta") or {},
                }
            )
        return {"items": items, "coming_soon": False}


__all__ = ["BillingService"]
