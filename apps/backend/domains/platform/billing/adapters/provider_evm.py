from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from domains.platform.billing.domain.models import Plan
from domains.platform.billing.ports import (
    CheckoutResult,
    ContractsRepo,
    CryptoConfigRepo,
    PaymentProvider,
)

logger = logging.getLogger(__name__)


class EVMProvider(PaymentProvider):
    """EVM (Ethereum-compatible) checkout provider."""

    def __init__(
        self,
        *,
        contracts: ContractsRepo,
        crypto_config: CryptoConfigRepo,
        default_config_slug: str = "default",
        fallback_webhook_secret: str | None = None,
        checkout_ttl_minutes: int = 15,
    ) -> None:
        self._contracts = contracts
        self._crypto_config = crypto_config
        self._config_slug = default_config_slug
        self._fallback_secret = fallback_webhook_secret
        self._checkout_ttl = max(1, checkout_ttl_minutes)

    async def checkout(self, user_id: str, plan: Plan) -> CheckoutResult:
        contract_slug = plan.contract_slug or plan.gateway_slug
        if not contract_slug:
            raise ValueError("contract_not_configured")

        contract = await self._contracts.get(contract_slug)
        if not contract:
            raise ValueError("contract_not_found")

        config_row = await self._crypto_config.get(self._config_slug)
        config = (config_row or {}).get("config") or {}
        rpc_endpoints = config.get("rpc_endpoints") or {}
        fallback_networks = config.get("fallback_networks") or {}

        evm_features = (plan.features or {}).get("evm") if plan.features else {}
        if not isinstance(evm_features, dict):
            evm_features = {}

        network = str(
            evm_features.get("network")
            or contract.get("chain")
            or contract.get("chain_id")
            or "ethereum"
        )
        token = evm_features.get("token") or plan.price_token

        amount_wei = self._resolve_amount_wei(plan, evm_features)
        calldata = evm_features.get("calldata")
        method = evm_features.get("method") or contract.get("mint_method")

        external_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(minutes=self._checkout_ttl)

        payload = {
            "chainId": contract.get("chain_id"),
            "network": network,
            "contract": {
                "slug": contract_slug,
                "address": contract.get("address"),
                "type": contract.get("type"),
            },
            "request": {
                "to": contract.get("address"),
                "value_wei": amount_wei,
                "token": token,
                "calldata": calldata,
                "method": method,
            },
            "rpc": {
                "primary": rpc_endpoints.get(network),
                "fallback": fallback_networks.get(network),
                "all": rpc_endpoints,
            },
        }

        deeplink = evm_features.get("deeplink_url")

        meta = {
            "network": network,
            "token": token,
            "contract_slug": contract_slug,
            "plan_slug": plan.slug,
            "user_id": user_id,
        }

        return CheckoutResult(
            url=deeplink,
            provider="evm",
            external_id=external_id,
            payload=payload,
            meta=meta,
            expires_at=expires_at.isoformat(),
        )

    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool:
        if not signature:
            logger.warning("Webhook signature missing for EVM provider")
            return False
        secret = await self._resolve_secret_from_payload(payload)
        if not secret:
            logger.warning("Webhook secret not configured for EVM provider")
            return False
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest.lower(), signature.lower())

    async def _resolve_secret_from_payload(self, payload: bytes) -> str | None:
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._fallback_secret

        contract_ref = (
            data.get("contract")
            or data.get("contract_slug")
            or data.get("contract_id")
            or data.get("contract_address")
        )
        if contract_ref:
            if isinstance(contract_ref, dict):
                contract_ref = (
                    contract_ref.get("slug")
                    or contract_ref.get("id")
                    or contract_ref.get("address")
                )
            if isinstance(contract_ref, str):
                contract = await self._contracts.get(contract_ref)
                if not contract and data.get("contract_address"):
                    contract = await self._contracts.get_by_address(
                        data["contract_address"]
                    )
                if contract:
                    secret = contract.get("webhook_secret")
                    if secret:
                        return str(secret)
        return self._fallback_secret

    @staticmethod
    def _resolve_amount_wei(plan: Plan, evm_features: dict[str, Any]) -> int:
        value = evm_features.get("amount_wei")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value, 0)
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass
        price_cents = plan.price_cents or 0
        # Rough estimate: treat 1 cent as 1e16 wei for stablecoins.
        try:
            return int(price_cents) * 10**16
        except (TypeError, ValueError):
            return 0


__all__ = ["EVMProvider"]
