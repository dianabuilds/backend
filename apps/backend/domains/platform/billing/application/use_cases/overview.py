from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.billing.application.service import BillingService
from domains.platform.billing.ports import LedgerRepo

from .metrics import MetricsAdminUseCase


@dataclass
class OverviewUseCases:
    metrics: MetricsAdminUseCase
    ledger: LedgerRepo
    service: BillingService

    async def dashboard(self) -> dict[str, Any]:
        kpi = await self.metrics.kpi()
        subscriptions = await self.metrics.metrics()
        revenue = await self.metrics.revenue_ts(days=30)
        return {
            "kpi": kpi,
            "subscriptions": subscriptions,
            "revenue": revenue.get("series") or [],
        }

    async def networks(self) -> dict[str, Any]:
        breakdown = await self.metrics.network_breakdown()
        return breakdown

    async def payouts(
        self, *, status: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        rows = await self.ledger.list_recent(limit=int(max(1, min(limit, 500))))
        normalized_status = (status or "").lower()
        items = []
        for row in rows:
            row_status = str(row.get("status") or "").lower()
            if normalized_status:
                if row_status != normalized_status:
                    continue
            else:
                if row_status in {"succeeded", "success", "captured", "completed"}:
                    continue
            items.append(row)
        return {"items": items}

    async def user_summary(self, *, user_id: str) -> dict[str, Any]:
        return await self.metrics.summary(user_id=user_id)

    async def user_history(self, *, user_id: str, limit: int) -> dict[str, Any]:
        return await self.metrics.history(user_id=user_id, limit=limit)

    async def crypto_config(self) -> dict[str, Any]:
        return await self.metrics.get_crypto_config()

    async def set_crypto_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.metrics.set_crypto_config(payload=payload)
