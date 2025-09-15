from __future__ import annotations

import uuid

from domains.platform.billing.domain.models import Plan
from domains.platform.billing.ports import (
    CheckoutResult,
    PaymentProvider,
)


class MockProvider(PaymentProvider):
    async def checkout(self, user_id: str, plan: Plan) -> CheckoutResult:
        # Return a fake external id and no external URL
        return CheckoutResult(url=None, provider="mock", external_id=str(uuid.uuid4()))

    async def verify_webhook(
        self, payload: bytes, signature: str | None
    ) -> bool:  # noqa: ARG002
        return True


__all__ = ["MockProvider"]
