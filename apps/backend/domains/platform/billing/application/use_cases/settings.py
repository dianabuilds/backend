from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from domains.platform.billing.application.service import BillingService
from domains.product.profile.application.profile_presenter import profile_to_dict

logger = logging.getLogger(__name__)


class ProfileServiceProtocol(Protocol):
    async def get_profile(self, user_id: str) -> Any: ...


@dataclass
class BillingSettingsUseCase:
    service: BillingService
    profile_service: ProfileServiceProtocol

    async def build_bundle(self, user_id: str) -> dict[str, Any]:
        summary = await self.service.get_summary_for_user(user_id)
        history = await self.service.get_history_for_user(user_id)
        wallet: dict[str, Any] | None = None
        try:
            profile_view = await self.profile_service.get_profile(user_id)
        except ValueError:
            wallet = None
        except Exception as exc:
            logger.exception(
                "Failed to fetch profile while building billing bundle", exc_info=exc
            )
            wallet = None
        else:
            profile_payload = profile_to_dict(profile_view)
            wallet_data = profile_payload.get("wallet") or {}
            if isinstance(wallet_data, dict):
                wallet = {
                    "address": wallet_data.get("address"),
                    "chain_id": wallet_data.get("chain_id"),
                    "verified_at": wallet_data.get("verified_at"),
                    "is_verified": bool(wallet_data.get("verified_at")),
                }
                wallet["status"] = "connected" if wallet.get("address") else "missing"
            else:
                wallet = None
        summary_payload = dict(summary)
        summary_payload["wallet"] = wallet
        payment = dict(summary_payload.get("payment") or {})
        payment.setdefault("mode", "evm_wallet")
        payment["status"] = (
            "wallet_connected" if wallet and wallet.get("address") else "wallet_missing"
        )
        summary_payload["payment"] = payment
        return {"summary": summary_payload, "history": history, "wallet": wallet}


__all__ = ["BillingSettingsUseCase", "ProfileServiceProtocol"]
