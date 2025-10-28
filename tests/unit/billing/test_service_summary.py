from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.service import BillingService
from apps.backend.domains.platform.billing.ports import BillingHistory, BillingSummary


def _make_service(
    *,
    summary: BillingSummary,
    history: BillingHistory,
) -> BillingService:
    plans = SimpleNamespace()
    subs = SimpleNamespace(get_active_for_user=AsyncMock())
    ledger = SimpleNamespace()
    provider = SimpleNamespace()
    summary_repo = SimpleNamespace(get_summary=AsyncMock(return_value=summary))
    history_repo = SimpleNamespace(get_history=AsyncMock(return_value=history))
    return BillingService(
        plans=plans,
        subs=subs,
        ledger=ledger,
        provider=provider,
        summary_repo=summary_repo,
        history_repo=history_repo,
    )


@pytest.mark.asyncio
async def test_summary_includes_debt_and_last_payment() -> None:
    now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    earlier = datetime(2024, 4, 15, 9, 30, tzinfo=timezone.utc)
    summary = BillingSummary(plan={"currency": "USD"}, subscription=None)
    history = BillingHistory(
        items=[
            {
                "id": "tx-success",
                "status": "succeeded",
                "created_at": now,
                "confirmed_at": now,
                "amount": 20.0,
                "amount_cents": 2000,
                "currency": "USD",
                "token": "USDC",
                "network": "polygon",
                "tx_hash": "0xabc",
                "provider": "evm",
                "product_type": "subscription_plan",
                "product_id": "plan-1",
                "gas": {"fee": 45, "token": "MATIC"},
                "failure_reason": None,
            },
            {
                "id": "tx-failed",
                "status": "failed",
                "created_at": earlier,
                "confirmed_at": None,
                "amount": 15.0,
                "amount_cents": 1500,
                "currency": "USD",
                "token": "USDC",
                "network": "polygon",
                "tx_hash": None,
                "provider": "evm",
                "product_type": "subscription_plan",
                "product_id": "plan-1",
                "gas": None,
                "failure_reason": "insufficient_funds",
            },
        ],
        coming_soon=False,
    )
    service = _make_service(summary=summary, history=history)

    result = await service.get_summary_for_user("user-1")

    assert result["last_payment"]["id"] == "tx-success"
    assert result["last_payment"]["gas"] == {"fee": 45, "token": "MATIC"}
    debt = result["debt"]
    assert debt["amount_cents"] == 1500
    assert pytest.approx(debt["amount"]) == 15.0
    assert debt["currency"] == "USD"
    assert debt["is_overdue"] is True
    assert debt["transactions"] == 1
    assert debt["last_issue"]["id"] == "tx-failed"


@pytest.mark.asyncio
async def test_summary_without_debt_marks_clear() -> None:
    summary = BillingSummary(plan=None, subscription=None)
    history = BillingHistory(items=[], coming_soon=False)
    service = _make_service(summary=summary, history=history)

    result = await service.get_summary_for_user("user-2")

    debt = result["debt"]
    assert debt["amount_cents"] == 0
    assert debt["amount"] is None
    assert debt["is_overdue"] is False
    assert debt["transactions"] == 0
    assert debt["last_issue"] is None
