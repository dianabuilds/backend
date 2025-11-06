from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from domains.platform.audit.application.service import AuditService
from domains.platform.audit.infrastructure import AuditLogPayload, safe_audit_log
from domains.platform.billing.ports import GatewayRepo, LedgerRepo

from .exceptions import BillingUseCaseError

logger = logging.getLogger(__name__)


@dataclass
class ProvidersAdminUseCase:
    gateways: GatewayRepo
    ledger: LedgerRepo
    audit_service: AuditService | None = None

    async def list_providers(self) -> dict[str, Any]:
        items = await self.gateways.list()
        return {"items": items}

    async def upsert_provider(
        self, *, payload: dict[str, Any], actor_id: str | None = None
    ) -> dict[str, Any]:
        slug = payload.get("slug")
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        base_config = payload.get("config") or {}
        if base_config and not isinstance(base_config, dict):
            try:
                base_config = dict(base_config)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Invalid provider config for %s: %s", slug, exc, exc_info=exc
                )
                base_config = {}
        data = {
            "slug": slug,
            "type": payload.get("type", "custom"),
            "enabled": payload.get("enabled", True),
            "priority": payload.get("priority", 100),
            "config": base_config,
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
        networks = payload.get("networks")
        if networks is not None:
            cfg = data.get("config") or {}
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["networks"] = networks
            data["config"] = cfg
        supported_tokens = payload.get("supported_tokens")
        if supported_tokens is not None:
            cfg = data.get("config") or {}
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["supported_tokens"] = supported_tokens
            data["config"] = cfg
        default_network = payload.get("default_network")
        if default_network is not None:
            cfg = data.get("config") or {}
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["default_network"] = default_network
            data["config"] = cfg
        item = await self.gateways.upsert(data)
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="billing.provider.upsert",
                resource_type="billing_provider",
                resource_id=item.get("slug"),
                after=item,
                extra={"route": "/v1/billing/admin/providers"},
            ),
            logger=logger,
            error_slug="billing_provider_audit_failed",
            suppressed=(Exception,),
            log_extra={"provider": slug},
        )
        return {"provider": item}

    async def delete_provider(
        self, *, slug: str, actor_id: str | None = None
    ) -> dict[str, Any]:
        if not slug:
            raise BillingUseCaseError(status_code=400, detail="slug_required")
        await self.gateways.delete(slug)
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="billing.provider.delete",
                resource_type="billing_provider",
                resource_id=slug,
                extra={"route": "/v1/billing/admin/providers"},
            ),
            logger=logger,
            error_slug="billing_provider_delete_audit_failed",
            suppressed=(Exception,),
            log_extra={"provider": slug},
        )
        return {"ok": True}

    async def list_transactions(self, *, limit: int = 100) -> dict[str, Any]:
        items = await self.ledger.list_recent(limit=int(limit))
        return {"items": items}


__all__ = ["ProvidersAdminUseCase"]
