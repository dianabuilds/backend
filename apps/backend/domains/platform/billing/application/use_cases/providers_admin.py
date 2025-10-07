from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from domains.platform.billing.ports import GatewayRepo, LedgerRepo

from .exceptions import BillingUseCaseError

logger = logging.getLogger(__name__)


@dataclass
class ProvidersAdminUseCase:
    gateways: GatewayRepo
    ledger: LedgerRepo

    async def list_providers(self) -> dict[str, Any]:
        items = await self.gateways.list()
        return {"items": items}

    async def upsert_provider(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        slug = payload.get("slug")
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        data = {
            "slug": slug,
            "type": payload.get("type", "custom"),
            "enabled": payload.get("enabled", True),
            "priority": payload.get("priority", 100),
            "config": payload.get("config") or {},
        }
        linked_contract = payload.get("contract_slug") or payload.get("linked_contract")
        if linked_contract:
            cfg: dict[str, Any] = {}
            existing_cfg = data.get("config")
            if existing_cfg:
                try:
                    cfg = dict(existing_cfg)
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "Invalid provider config for %s: %s", slug, exc, exc_info=exc
                    )
                    cfg = {}
            cfg["linked_contract"] = str(linked_contract)
            data["config"] = cfg
        item = await self.gateways.upsert(data)
        return {"provider": item}

    async def delete_provider(self, *, slug: str) -> dict[str, Any]:
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        await self.gateways.delete(slug)
        return {"ok": True}

    async def list_transactions(self, *, limit: int = 100) -> dict[str, Any]:
        items = await self.ledger.list_recent(limit=int(limit))
        return {"items": items}


__all__ = ["ProvidersAdminUseCase"]
