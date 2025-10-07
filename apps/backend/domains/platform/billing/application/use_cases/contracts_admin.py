from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.billing.ports import ContractsRepo

from .exceptions import BillingUseCaseError


@dataclass
class ContractsAdminUseCase:
    contracts: ContractsRepo

    async def list_contracts(self) -> dict[str, Any]:
        items = await self.contracts.list()
        return {"items": items}

    async def upsert_contract(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        slug = payload.get("slug") or payload.get("address") or payload.get("title")
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        data = {
            "id": payload.get("id"),
            "slug": slug,
            "title": payload.get("title"),
            "chain": payload.get("chain"),
            "address": payload.get("address"),
            "type": payload.get("type"),
            "enabled": payload.get("enabled", True),
            "status": payload.get("status", "active"),
            "testnet": payload.get("testnet", False),
            "methods": payload.get("methods"),
            "abi": payload.get("abi"),
            "abi_present": bool(payload.get("abi") is not None),
            "webhook_url": payload.get("webhook_url"),
        }
        item = await self.contracts.upsert(data)
        return {"contract": item}

    async def delete_contract(self, *, id_or_slug: str) -> dict[str, Any]:
        if not id_or_slug:
            raise BillingUseCaseError(status_code=400, detail="contract_required")
        await self.contracts.delete(id_or_slug)
        return {"ok": True}

    async def list_events(self, *, id_or_slug: str, limit: int = 100) -> dict[str, Any]:
        items = await self.contracts.list_events(id_or_slug, limit=int(limit))
        return {"items": items}

    async def add_event(
        self, *, id_or_slug: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        contract = await self.contracts.get(id_or_slug)
        if not contract:
            raise BillingUseCaseError(status_code=404, detail="contract_not_found")
        event = {
            "contract_id": contract["id"],
            "event": payload.get("event") or "event",
            "method": payload.get("method"),
            "tx_hash": payload.get("tx_hash"),
            "status": payload.get("status"),
            "amount": payload.get("amount"),
            "token": payload.get("token"),
            "meta": payload.get("meta") or {},
        }
        await self.contracts.add_event(event)
        return {"ok": True}

    async def list_all_events(self, *, limit: int = 100) -> dict[str, Any]:
        items = await self.contracts.list_events(None, limit=int(limit))
        return {"items": items}

    async def metrics_methods(
        self, *, id_or_slug: str | None, window: int = 1000
    ) -> dict[str, Any]:
        methods = await self.contracts.metrics_methods(id_or_slug, window=int(window))
        return {"methods": methods}

    async def metrics_timeseries(
        self, *, id_or_slug: str | None, days: int = 30
    ) -> dict[str, Any]:
        methods = await self.contracts.metrics_methods_ts(id_or_slug, days=int(days))
        volume = await self.contracts.metrics_volume_ts(id_or_slug, days=int(days))
        return {"methods": methods, "volume": volume}


__all__ = ["ContractsAdminUseCase"]
