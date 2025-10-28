from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from domains.platform.audit.application.service import AuditService
from domains.platform.audit.infrastructure import AuditLogPayload, safe_audit_log
from domains.platform.billing.ports import ContractsRepo

from .exceptions import BillingUseCaseError

logger = logging.getLogger(__name__)


@dataclass
class ContractsAdminUseCase:
    contracts: ContractsRepo
    audit_service: AuditService | None = None

    async def list_contracts(self) -> dict[str, Any]:
        items = await self.contracts.list()
        return {"items": items}

    async def upsert_contract(
        self, *, payload: dict[str, Any], actor_id: str | None = None
    ) -> dict[str, Any]:
        slug = payload.get("slug") or payload.get("address") or payload.get("title")
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        methods = payload.get("methods")
        if methods is not None and not isinstance(methods, dict):
            try:
                methods = dict(methods)
            except (TypeError, ValueError) as exc:
                raise BillingUseCaseError(
                    status_code=400, detail="invalid_methods"
                ) from exc
        fallback_rpc = payload.get("fallback_rpc")
        if fallback_rpc is not None and not isinstance(fallback_rpc, dict):
            try:
                fallback_rpc = dict(fallback_rpc)
            except (TypeError, ValueError) as exc:
                raise BillingUseCaseError(
                    status_code=400, detail="invalid_fallback_rpc"
                ) from exc
        data = {
            "id": payload.get("id"),
            "slug": slug,
            "title": payload.get("title"),
            "chain": payload.get("chain"),
            "chain_id": payload.get("chain_id"),
            "address": payload.get("address"),
            "type": payload.get("type"),
            "enabled": payload.get("enabled", True),
            "status": payload.get("status", "active"),
            "testnet": payload.get("testnet", False),
            "methods": methods,
            "mint_method": payload.get("mint_method"),
            "burn_method": payload.get("burn_method"),
            "abi": payload.get("abi"),
            "abi_present": bool(payload.get("abi") is not None),
            "webhook_url": payload.get("webhook_url"),
            "webhook_secret": payload.get("webhook_secret"),
            "fallback_rpc": fallback_rpc,
        }
        item = await self.contracts.upsert(data)
        resource_id = item.get("slug") or item.get("id")
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="billing.contract.upsert",
                resource_type="billing_contract",
                resource_id=resource_id,
                after=item,
                extra={"route": "/v1/billing/admin/contracts"},
            ),
            logger=logger,
            error_slug="billing_contract_audit_failed",
            suppressed=(Exception,),
            log_extra={"contract": resource_id},
        )
        return {"contract": item}

    async def delete_contract(
        self, *, id_or_slug: str, actor_id: str | None = None
    ) -> dict[str, Any]:
        if not id_or_slug:
            raise BillingUseCaseError(status_code=400, detail="contract_required")
        await self.contracts.delete(id_or_slug)
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="billing.contract.delete",
                resource_type="billing_contract",
                resource_id=id_or_slug,
                extra={"route": "/v1/billing/admin/contracts"},
            ),
            logger=logger,
            error_slug="billing_contract_delete_audit_failed",
            suppressed=(Exception,),
            log_extra={"contract": id_or_slug},
        )
        return {"ok": True}

    async def list_events(self, *, id_or_slug: str, limit: int = 100) -> dict[str, Any]:
        items = await self.contracts.list_events(id_or_slug, limit=int(limit))
        return {"items": items}

    async def add_event(
        self,
        *,
        id_or_slug: str,
        payload: dict[str, Any],
        actor_id: str | None = None,
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
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="billing.contract.event.add",
                resource_type="billing_contract_event",
                resource_id=contract.get("id"),
                after=event,
                extra={"route": "/v1/billing/admin/contracts/events"},
            ),
            logger=logger,
            error_slug="billing_contract_event_audit_failed",
            suppressed=(Exception,),
            log_extra={"contract": contract.get("id")},
        )
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
