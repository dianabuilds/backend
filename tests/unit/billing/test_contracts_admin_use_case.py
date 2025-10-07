from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.contracts_admin import (
    ContractsAdminUseCase,
)
from apps.backend.domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)


@pytest.mark.asyncio
async def test_list_contracts_returns_items() -> None:
    repo = SimpleNamespace(list=AsyncMock(return_value=[{"id": "c1"}]))
    use_case = ContractsAdminUseCase(contracts=repo)

    result = await use_case.list_contracts()

    assert result == {"items": [{"id": "c1"}]}
    repo.list.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_requires_slug() -> None:
    use_case = ContractsAdminUseCase(contracts=SimpleNamespace())
    with pytest.raises(BillingUseCaseError):
        await use_case.upsert_contract(payload={})


@pytest.mark.asyncio
async def test_upsert_populates_payload() -> None:
    repo = SimpleNamespace(upsert=AsyncMock(return_value={"id": "c1", "slug": "token"}))
    use_case = ContractsAdminUseCase(contracts=repo)
    payload = {
        "title": "Payment",
        "address": "0xabc",
        "methods": ["mint"],
        "abi": {"contract": "demo"},
    }

    result = await use_case.upsert_contract(payload=payload)

    assert result == {"contract": {"id": "c1", "slug": "token"}}
    sent = repo.upsert.call_args.args[0]
    assert sent["slug"] == "0xabc"
    assert sent["abi_present"] is True


@pytest.mark.asyncio
async def test_delete_requires_identifier() -> None:
    use_case = ContractsAdminUseCase(contracts=SimpleNamespace())
    with pytest.raises(BillingUseCaseError):
        await use_case.delete_contract(id_or_slug="")


@pytest.mark.asyncio
async def test_add_event_requires_existing_contract() -> None:
    repo = SimpleNamespace(
        get=AsyncMock(return_value=None),
        get_by_address=AsyncMock(return_value=None),
        add_event=AsyncMock(),
    )
    use_case = ContractsAdminUseCase(contracts=repo)

    with pytest.raises(BillingUseCaseError):
        await use_case.add_event(id_or_slug="missing", payload={})
    repo.add_event.assert_not_called()


@pytest.mark.asyncio
async def test_add_event_persists_event() -> None:
    repo = SimpleNamespace(
        get=AsyncMock(return_value={"id": "contract-1"}),
        get_by_address=AsyncMock(return_value=None),
        add_event=AsyncMock(),
    )
    use_case = ContractsAdminUseCase(contracts=repo)

    payload = {"event": "PaymentReceived", "meta": {"currency": "USD"}}
    result = await use_case.add_event(id_or_slug="contract-1", payload=payload)

    assert result == {"ok": True}
    repo.add_event.assert_awaited_once()
    event_payload = repo.add_event.call_args.args[0]
    assert event_payload["contract_id"] == "contract-1"
    assert event_payload["event"] == "PaymentReceived"
    assert event_payload["meta"] == {"currency": "USD"}


@pytest.mark.asyncio
async def test_metrics_timeseries_fetches_methods_and_volume() -> None:
    repo = SimpleNamespace(
        metrics_methods=AsyncMock(return_value=[{"method": "mint"}]),
        metrics_methods_ts=AsyncMock(return_value=[1, 2, 3]),
        metrics_volume_ts=AsyncMock(return_value=[10, 20]),
    )
    use_case = ContractsAdminUseCase(contracts=repo)

    result = await use_case.metrics_timeseries(id_or_slug=None, days=7)

    assert result == {"methods": [1, 2, 3], "volume": [10, 20]}
    repo.metrics_methods_ts.assert_awaited_once_with(None, days=7)
    repo.metrics_volume_ts.assert_awaited_once_with(None, days=7)
