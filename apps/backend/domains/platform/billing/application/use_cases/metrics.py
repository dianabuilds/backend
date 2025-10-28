from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.billing.application.service import BillingService
from domains.platform.billing.ports import BillingAnalyticsRepo, CryptoConfigRepo


@dataclass
class MetricsAdminUseCase:
    service: BillingService
    analytics: BillingAnalyticsRepo
    crypto_store: CryptoConfigRepo

    async def summary(self, *, user_id: str) -> dict[str, Any]:
        return await self.service.get_summary_for_user(user_id)

    async def history(self, *, user_id: str, limit: int) -> dict[str, Any]:
        return await self.service.get_history_for_user(user_id, limit=limit)

    async def kpi(self) -> dict[str, Any]:
        return await self.analytics.kpi()

    async def metrics(self) -> dict[str, Any]:
        return await self.analytics.subscription_metrics()

    async def revenue_ts(self, *, days: int = 30) -> dict[str, Any]:
        series = await self.analytics.revenue_timeseries(days=days)
        return {"series": series}

    async def network_breakdown(self) -> dict[str, Any]:
        rows = await self.analytics.network_breakdown()
        return {"networks": rows}

    async def get_crypto_config(self) -> dict[str, Any]:
        row = await self.crypto_store.get("default")
        return {"config": (row or {}).get("config") or {}}

    async def set_crypto_config(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        base_row = await self.crypto_store.get("default")
        base = dict((base_row or {}).get("config") or {})
        base.update(
            {
                "rpc_endpoints": payload.get("rpc_endpoints")
                or base.get("rpc_endpoints")
                or {},
                "retries": (
                    payload.get("retries")
                    if payload.get("retries") is not None
                    else base.get("retries")
                ),
                "gas_price_cap": (
                    payload.get("gas_price_cap")
                    if payload.get("gas_price_cap") is not None
                    else base.get("gas_price_cap")
                ),
                "fallback_networks": payload.get("fallback_networks")
                or base.get("fallback_networks")
                or {},
            }
        )
        row = await self.crypto_store.set("default", base)
        return {"config": row.get("config") or {}}


__all__ = ["MetricsAdminUseCase"]
