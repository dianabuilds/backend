from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from apps.backend.domains.platform.billing.domain.models import Plan, Subscription
from apps.backend.domains.platform.billing.application.service import BillingService


def _make_service(
    *,
    ledger: SimpleNamespace,
    provider: SimpleNamespace,
    plans: SimpleNamespace | None = None,
    subs: SimpleNamespace | None = None,
    events: SimpleNamespace | None = None,
    notify: Any | None = None,
    audit: Any | None = None,
    finance_ops_user_id: str | None = None,
) -> BillingService:
    plan_repo = plans or SimpleNamespace(
        get_by_slug=AsyncMock(return_value=None),
        get_by_id=AsyncMock(return_value=None),
    )
    subs_repo = subs or SimpleNamespace(
        get_active_for_user=AsyncMock(return_value=None),
        activate=AsyncMock(return_value=None),
    )
    return BillingService(
        plans=plan_repo,
        subs=subs_repo,
        ledger=ledger,
        provider=provider,
        summary_repo=SimpleNamespace(get_summary=AsyncMock()),
        history_repo=SimpleNamespace(get_history=AsyncMock()),
        events=events,
        notify_service=notify,
        audit_service=audit,
        finance_ops_recipient=finance_ops_user_id,
    )


def _sample_plan(plan_id: str = "plan-basic") -> Plan:
    now = datetime.now(timezone.utc)
    return Plan(
        id=plan_id,
        slug="basic",
        title="Basic",
        price_cents=5000,
        currency="USD",
        is_active=True,
        order=1,
        monthly_limits={"requests": 1000},
        features={"feature": True},
        created_at=now,
        updated_at=now,
        price_token="USDC",
        price_usd_estimate=50.0,
        billing_interval="month",
        gateway_slug="evm",
        contract_slug="contract-basic",
    )


def _sample_subscription(plan_id: str) -> Subscription:
    now = datetime.now(timezone.utc)
    return Subscription(
        id="sub-1",
        user_id="user-1",
        plan_id=plan_id,
        status="active",
        auto_renew=True,
        started_at=now,
        ends_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_handle_webhook_updates_pending_transaction() -> None:
    ledger = SimpleNamespace(
        get_by_tx_hash=AsyncMock(return_value=None),
        get_by_external_id=AsyncMock(
            return_value={"id": "tx-1", "status": "pending", "tx_hash": None}
        ),
        update_transaction=AsyncMock(
            return_value={"id": "tx-1", "status": "succeeded"}
        ),
        add_tx=AsyncMock(),
        list_pending=AsyncMock(return_value=[]),
    )
    provider = SimpleNamespace(verify_webhook=AsyncMock(return_value=True))
    service = _make_service(ledger=ledger, provider=provider)

    payload = {
        "external_id": "checkout-1",
        "tx_hash": "0xabc",
        "status": "succeeded",
        "network": "polygon",
        "token": "USDC",
    }
    result = await service.handle_webhook(
        json.dumps(payload).encode("utf-8"), signature="sig"
    )

    assert result["updated"]
    provider.verify_webhook.assert_awaited_once()
    ledger.update_transaction.assert_awaited_once()
    args, kwargs = ledger.update_transaction.await_args
    assert args[0] == "tx-1"
    assert kwargs["status"] == "succeeded"
    assert kwargs["tx_hash"] == "0xabc"


@pytest.mark.asyncio
async def test_handle_webhook_success_triggers_integrations() -> None:
    plan = _sample_plan()
    subscription = _sample_subscription(plan.id)
    ledger = SimpleNamespace(
        get_by_tx_hash=AsyncMock(
            return_value={
                "id": "tx-1",
                "status": "pending",
                "user_id": "user-1",
                "gross_cents": 5000,
                "currency": "USD",
                "gateway_slug": "evm",
                "meta": {"plan": {"id": plan.id, "slug": plan.slug}},
            }
        ),
        get_by_external_id=AsyncMock(return_value=None),
        update_transaction=AsyncMock(
            return_value={
                "id": "tx-1",
                "status": "succeeded",
                "user_id": "user-1",
                "gross_cents": 5000,
                "currency": "USD",
                "gateway_slug": "evm",
                "tx_hash": "0xabc",
                "meta": {"plan": {"id": plan.id, "slug": plan.slug}},
            }
        ),
        add_tx=AsyncMock(),
        list_pending=AsyncMock(return_value=[]),
    )
    provider = SimpleNamespace(verify_webhook=AsyncMock(return_value=True))
    events = SimpleNamespace(publish=Mock())
    notify = SimpleNamespace(create_notification=AsyncMock(return_value={"id": "n"}))
    audit = SimpleNamespace(log=AsyncMock())
    subs = SimpleNamespace(
        get_active_for_user=AsyncMock(return_value=None),
        activate=AsyncMock(return_value=subscription),
    )
    plans = SimpleNamespace(
        get_by_slug=AsyncMock(return_value=plan),
        get_by_id=AsyncMock(return_value=plan),
    )
    service = _make_service(
        ledger=ledger,
        provider=provider,
        plans=plans,
        subs=subs,
        events=events,
        notify=notify,
        audit=audit,
        finance_ops_user_id="finance",
    )
    payload = {
        "external_id": "checkout-1",
        "tx_hash": "0xabc",
        "status": "succeeded",
        "user_id": "user-1",
        "plan_slug": plan.slug,
        "plan_id": plan.id,
        "amount_cents": 5000,
        "currency": "USD",
        "network": "polygon",
        "token": "USDC",
    }
    result = await service.handle_webhook(
        json.dumps(payload).encode("utf-8"), signature="sig"
    )
    assert result["updated"]
    events.publish.assert_called_once()
    topic, event_payload, key = events.publish.call_args.args
    assert topic == "billing.plan.changed.v1"
    assert key == "user-1"
    assert event_payload["plan"]["slug"] == plan.slug
    notify_calls = [
        call.args[0].user_id for call in notify.create_notification.await_args_list
    ]
    assert notify_calls == ["user-1", "finance"]
    subs.activate.assert_awaited_once_with("user-1", plan.id)
    assert audit.log.await_count >= 1


@pytest.mark.asyncio
async def test_handle_webhook_duplicate_detection() -> None:
    ledger = SimpleNamespace(
        get_by_tx_hash=AsyncMock(
            return_value={"id": "tx-1", "status": "succeeded", "tx_hash": "0xabc"}
        ),
        get_by_external_id=AsyncMock(return_value=None),
        update_transaction=AsyncMock(),
        add_tx=AsyncMock(),
        list_pending=AsyncMock(return_value=[]),
    )
    provider = SimpleNamespace(verify_webhook=AsyncMock(return_value=True))
    service = _make_service(ledger=ledger, provider=provider)

    payload = {"tx_hash": "0xabc", "status": "succeeded"}
    result = await service.handle_webhook(
        json.dumps(payload).encode("utf-8"), signature="sig"
    )

    assert result["duplicate"]
    ledger.update_transaction.assert_not_called()
    ledger.add_tx.assert_not_called()


@pytest.mark.asyncio
async def test_handle_webhook_inserts_when_missing() -> None:
    ledger = SimpleNamespace(
        get_by_tx_hash=AsyncMock(return_value=None),
        get_by_external_id=AsyncMock(return_value=None),
        update_transaction=AsyncMock(),
        add_tx=AsyncMock(),
        list_pending=AsyncMock(return_value=[]),
    )
    provider = SimpleNamespace(verify_webhook=AsyncMock(return_value=True))
    service = _make_service(ledger=ledger, provider=provider)

    payload = {
        "tx_hash": "0xaaa",
        "status": "FAILED",
        "user_id": "user-1",
        "plan_id": "plan-1",
        "amount_cents": 500,
    }
    result = await service.handle_webhook(
        json.dumps(payload).encode("utf-8"), signature="sig"
    )

    assert result["created"]
    ledger.add_tx.assert_awaited_once()
    args, _ = ledger.add_tx.await_args
    tx_payload = args[0]
    assert tx_payload["user_id"] == "user-1"
    assert tx_payload["status"] == "failed"
    assert tx_payload["tx_hash"] == "0xaaa"


@pytest.mark.asyncio
async def test_reconcile_pending_transactions_updates_retry_count() -> None:
    pending = [
        {
            "id": "tx-1",
            "status": "pending",
            "tx_hash": None,
            "network": None,
            "token": None,
            "confirmed_at": None,
            "failure_reason": None,
            "meta": {"retries": 1},
        }
    ]
    ledger = SimpleNamespace(
        get_by_tx_hash=AsyncMock(),
        get_by_external_id=AsyncMock(),
        update_transaction=AsyncMock(return_value=pending[0]),
        add_tx=AsyncMock(),
        list_pending=AsyncMock(return_value=pending),
    )
    provider = SimpleNamespace(verify_webhook=AsyncMock())
    service = _make_service(ledger=ledger, provider=provider)

    result = await service.reconcile_pending_transactions(
        older_than_seconds=10, limit=5
    )

    assert result["count"] == 1
    ledger.update_transaction.assert_awaited_once()
