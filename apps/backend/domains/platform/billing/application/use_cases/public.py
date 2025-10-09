from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from domains.platform.billing.application.service import BillingService
from domains.platform.billing.ports import ContractsRepo

from .exceptions import BillingUseCaseError


@dataclass
class PublicBillingUseCases:
    service: BillingService
    contracts: ContractsRepo
    webhook_secret: str | None

    async def list_plans(self) -> dict[str, Any]:
        plans = await self.service.list_plans()
        return {"items": [plan.__dict__ for plan in plans]}

    async def checkout(
        self, *, user_id: str | None, plan_slug: str | None
    ) -> dict[str, Any]:
        if not user_id:
            raise BillingUseCaseError(status_code=401, detail="unauthenticated")
        if not plan_slug:
            raise BillingUseCaseError(status_code=400, detail="plan_required")
        result = await self.service.checkout(user_id, plan_slug)
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
        event = {
            "contract_id": contract["id"],
            "event": payload.get("event") or "PaymentReceived",
            "method": payload.get("method"),
            "tx_hash": payload.get("tx_hash"),
            "status": payload.get("status"),
            "amount": payload.get("amount"),
            "token": payload.get("token"),
            "meta": payload.get("meta") or {},
        }
        await contracts.add_event(event)
        return {"ok": True}


__all__ = ["PublicBillingUseCases"]
