from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from apps.backend.domains.platform.billing.application.use_cases.public import (
    PublicBillingUseCases,
)


@dataclass
class DummyPlan:
    id: str
    slug: str
    title: str
    price_cents: int = 0


@dataclass
class DummyCheckoutResult:
    url: str | None
    provider: str
    external_id: str


class DummyService:
    def __init__(self) -> None:
        self.list_plans = AsyncMock()
        self.checkout = AsyncMock()
        self.get_subscription_for_user = AsyncMock()
        self.get_summary_for_user = AsyncMock()
        self.get_history_for_user = AsyncMock()
        self.handle_webhook = AsyncMock()


class DummyContracts:
    def __init__(self) -> None:
        self.get = AsyncMock()
        self.get_by_address = AsyncMock()
        self.add_event = AsyncMock()


@pytest.mark.asyncio
async def test_list_plans_serializes_items() -> None:
    service = DummyService()
    plans = [DummyPlan(id="p1", slug="basic", title="Basic")]
    service.list_plans.return_value = plans
    use_cases = PublicBillingUseCases(
        service=service, contracts=DummyContracts(), webhook_secret=None
    )

    result = await use_cases.list_plans()

    assert result == {"items": [plans[0].__dict__]}
    service.list_plans.assert_awaited_once()


@pytest.mark.asyncio
async def test_checkout_requires_authentication() -> None:
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=None
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.checkout(user_id=None, plan_slug="pro")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_checkout_requires_plan_slug() -> None:
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=None
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.checkout(user_id="user-1", plan_slug=None)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_checkout_returns_checkout_payload() -> None:
    service = DummyService()
    checkout_result = DummyCheckoutResult(
        url="https://pay", provider="mock", external_id="ext"
    )
    service.checkout.return_value = checkout_result
    use_cases = PublicBillingUseCases(
        service=service, contracts=DummyContracts(), webhook_secret=None
    )

    result = await use_cases.checkout(user_id="user-1", plan_slug="starter")

    assert result == {"ok": True, "checkout": checkout_result.__dict__}
    service.checkout.assert_awaited_once_with("user-1", "starter")


@pytest.mark.asyncio
async def test_get_my_summary_requires_auth() -> None:
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=None
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.get_my_summary(user_id=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_handle_contracts_webhook_validates_signature() -> None:
    body = b'{"contract": "c-1"}'
    secret = "super-secret"
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    service = DummyService()
    contracts = DummyContracts()
    contracts.get.return_value = {"id": "c-1"}
    use_cases = PublicBillingUseCases(
        service=service, contracts=contracts, webhook_secret=secret
    )

    result = await use_cases.handle_contracts_webhook(
        raw_body=body, signature=signature
    )

    assert result == {"ok": True}
    contracts.get.assert_awaited_once_with("c-1")
    contracts.add_event.assert_awaited_once()
    added_event = contracts.add_event.call_args.args[0]
    assert added_event["contract_id"] == "c-1"


@pytest.mark.asyncio
async def test_handle_contracts_webhook_requires_signature() -> None:
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret="secret"
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.handle_contracts_webhook(raw_body=b"{}", signature=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_handle_contracts_webhook_requires_secret() -> None:
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=None
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.handle_contracts_webhook(raw_body=b"{}", signature="sig")
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_handle_contracts_webhook_checks_signature_mismatch() -> None:
    secret = "secret"
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=secret
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.handle_contracts_webhook(raw_body=b"{}", signature="deadbeef")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_handle_contracts_webhook_invalid_json() -> None:
    secret = "secret"
    signature = hmac.new(
        secret.encode("utf-8"), b"not-json", hashlib.sha256
    ).hexdigest()
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=DummyContracts(), webhook_secret=secret
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.handle_contracts_webhook(
            raw_body=b"not-json", signature=signature
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_handle_contracts_webhook_missing_contract() -> None:
    secret = "secret"
    payload = b'{"event": "Payment"}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    contracts = DummyContracts()
    contracts.get.return_value = None
    contracts.get_by_address.return_value = None
    use_cases = PublicBillingUseCases(
        service=DummyService(), contracts=contracts, webhook_secret=secret
    )

    with pytest.raises(BillingUseCaseError) as exc:
        await use_cases.handle_contracts_webhook(raw_body=payload, signature=signature)
    assert exc.value.status_code == 404
    contracts.add_event.assert_not_called()
