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
        wallet: Any = None
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
            wallet = profile_to_dict(profile_view).get("wallet")
        return {"summary": summary, "history": history, "wallet": wallet}


__all__ = ["BillingSettingsUseCase", "ProfileServiceProtocol"]
