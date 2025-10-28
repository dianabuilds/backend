from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from typing import Any

from domains.platform.billing.application.service import BillingService
from domains.platform.billing.ports import ContractsRepo

from .exceptions import BillingUseCaseError

logger = logging.getLogger(__name__)


@dataclass
class PublicBillingUseCases:
    service: BillingService
    contracts: ContractsRepo
    webhook_secret: str | None

    async def list_plans(self) -> dict[str, Any]:
        plans = await self.service.list_plans()
        return {"items": [plan.__dict__ for plan in plans]}

    async def checkout(
        self,
        *,
        user_id: str | None,
        plan_slug: str | None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not user_id:
            raise BillingUseCaseError(status_code=401, detail="unauthenticated")
        if not plan_slug:
            raise BillingUseCaseError(status_code=400, detail="plan_required")
        idem_key = idempotency_key.strip() if idempotency_key else None
        logger.debug(
            "Billing checkout requested",
            extra={
                "plan_slug": plan_slug,
                "user_id": user_id,
                "idempotency_key": idem_key,
            },
        )
        try:
            result = await self.service.checkout(
                user_id=user_id,
                plan_slug=plan_slug,
                idempotency_key=idem_key,
            )
        except ValueError as exc:
            logger.warning(
                "Billing checkout failed",
                exc_info=exc,
                extra={
                    "plan_slug": plan_slug,
                    "user_id": user_id,
                    "idempotency_key": idem_key,
                },
            )
            detail = str(exc) or "checkout_failed"
            raise BillingUseCaseError(status_code=400, detail=detail) from exc
        return {"ok": True, "checkout": result.__dict__}

    async def get_my_subscription(self, *, user_id: str | None) -> dict[str, Any]:
        if not user_id:
            raise BillingUseCaseError(status_code=401, detail="unauthenticated")
        subscription = await self.service.get_subscription_for_user(user_id)
        return {"subscription": subscription}

    async def get_my_summary(self, *, user_id: str | None) -> dict[str, Any]:
        if not user_id:
            raise BillingUseCaseError(status_code=401, detail="unauthenticated")
        return await self.service.get_summary_for_user(user_id)

    async def get_my_history(
        self, *, user_id: str | None, limit: int = 20
    ) -> dict[str, Any]:
        if not user_id:
            raise BillingUseCaseError(status_code=401, detail="unauthenticated")
        return await self.service.get_history_for_user(user_id, limit=limit)

    async def get_summary_for_user(self, *, user_id: str) -> dict[str, Any]:
        return await self.service.get_summary_for_user(user_id)

    async def get_history_for_user(self, *, user_id: str, limit: int) -> dict[str, Any]:
        return await self.service.get_history_for_user(user_id, limit=limit)

    async def handle_webhook(
        self, *, payload: bytes, signature: str | None
    ) -> dict[str, Any]:
        return await self.service.handle_webhook(payload, signature)

    async def handle_contracts_webhook(
        self, *, raw_body: bytes, signature: str | None
    ) -> dict[str, Any]:
        if not signature:
            raise BillingUseCaseError(status_code=401, detail="missing_signature")
        secret = self.webhook_secret
        if not secret:
            raise BillingUseCaseError(
                status_code=503, detail="webhook_secret_not_configured"
            )
        calc = hmac.new(
            str(secret).encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if calc.lower() != str(signature).lower():
            raise BillingUseCaseError(status_code=403, detail="invalid_signature")
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise BillingUseCaseError(status_code=400, detail="invalid_json") from exc
        contracts = self.contracts
        id_or_slug = str(payload.get("contract")) if payload.get("contract") else None
        address = str(payload.get("address")) if payload.get("address") else None
        contract = None
        if id_or_slug:
            contract = await contracts.get(id_or_slug)
        if not contract and address:
            contract = await contracts.get_by_address(address)
        if not contract:
            raise BillingUseCaseError(status_code=404, detail="contract_not_found")
        methods = contract.get("methods") or {}
        if payload.get("method"):
            method = str(payload.get("method"))
            allowed_methods = set()
            if isinstance(methods, dict):
                allowed_methods = {str(key).lower() for key in methods.keys()}
            if allowed_methods and method.lower() not in allowed_methods:
                raise BillingUseCaseError(status_code=400, detail="unknown_method")
        meta = payload.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        raw_payload = dict(payload)
        if "meta" in raw_payload:
            raw_payload["meta_snapshot"] = raw_payload.pop("meta")
        meta.setdefault("raw_payload", raw_payload)
        status_raw = payload.get("status")
        status_normalized = (
            status_raw.lower() if isinstance(status_raw, str) else status_raw
        )
        event = {
            "contract_id": contract["id"],
            "event": payload.get("event") or "PaymentReceived",
            "method": payload.get("method"),
            "tx_hash": payload.get("tx_hash"),
            "status": status_normalized,
            "amount": payload.get("amount"),
            "token": payload.get("token"),
            "chain_id": contract.get("chain_id"),
            "meta": meta,
        }
        await contracts.add_event(event)
        logger.debug(
            "Contract webhook event recorded",
            extra={
                "contract_id": contract.get("id"),
                "contract_slug": contract.get("slug"),
                "tx_hash": payload.get("tx_hash"),
                "status": status_normalized,
                "event": event.get("event"),
            },
        )
        return {"ok": True}


__all__ = ["PublicBillingUseCases"]
