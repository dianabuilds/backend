from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.service import BillingService
from apps.backend.domains.platform.billing.domain.models import Plan
from apps.backend.domains.platform.billing.ports import CheckoutResult


@pytest.mark.asyncio
async def test_checkout_records_pending_transaction() -> None:
    plan = Plan(
        id="plan-1",
        slug="basic",
        title="Basic",
        price_cents=1500,
        currency="USD",
        is_active=True,
        order=1,
        monthly_limits=None,
        features={"evm": {"network": "polygon", "token": "USDC"}},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        price_token="USDC",
        billing_interval="month",
        gateway_slug="evm-gateway",
        contract_slug="billing-contract",
    )

    plans = SimpleNamespace(get_by_slug=AsyncMock(return_value=plan))
    subs = SimpleNamespace()
    ledger = SimpleNamespace(add_tx=AsyncMock())
    provider_result = CheckoutResult(
        url=None,
        provider="evm",
        external_id="ext-123",
        payload={"chainId": 137},
        meta={"network": "polygon", "token": "USDC"},
    )
    provider = SimpleNamespace(checkout=AsyncMock(return_value=provider_result))
    summary_repo = SimpleNamespace()
    history_repo = SimpleNamespace()

    service = BillingService(
        plans=plans,
        subs=subs,
        ledger=ledger,
        provider=provider,
        summary_repo=summary_repo,
        history_repo=history_repo,
    )

    result = await service.checkout("user-1", "basic", idempotency_key="idem-123")

    assert result == provider_result
    plans.get_by_slug.assert_awaited_once_with("basic")
    provider.checkout.assert_awaited_once_with("user-1", plan)
    ledger.add_tx.assert_awaited_once()
    payload = ledger.add_tx.await_args.args[0]
    assert payload["user_id"] == "user-1"
    assert payload["product_id"] == "plan-1"
    assert payload["status"] == "pending"
    assert payload["meta"]["idempotency_key"] == "idem-123"
    assert payload["meta"]["checkout_external_id"] == "ext-123"
    assert payload["token"] == "USDC"
    assert payload["network"] == "polygon"
