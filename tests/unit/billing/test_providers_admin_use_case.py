from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from apps.backend.domains.platform.billing.application.use_cases.providers_admin import (
    ProvidersAdminUseCase,
)


@pytest.mark.asyncio
async def test_list_providers_returns_items() -> None:
    gateways = SimpleNamespace(list=AsyncMock(return_value=[{"slug": "demo"}]))
    use_case = ProvidersAdminUseCase(
        gateways=gateways, ledger=SimpleNamespace(list_recent=AsyncMock())
    )

    result = await use_case.list_providers()

    assert result == {"items": [{"slug": "demo"}]}
    gateways.list.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_requires_slug() -> None:
    use_case = ProvidersAdminUseCase(
        gateways=SimpleNamespace(),
        ledger=SimpleNamespace(list_recent=AsyncMock()),
    )
    with pytest.raises(BillingUseCaseError):
        await use_case.upsert_provider(payload={})


@pytest.mark.asyncio
async def test_upsert_merges_linked_contract(caplog) -> None:
    gateways = SimpleNamespace(upsert=AsyncMock(return_value={"slug": "provider"}))
    use_case = ProvidersAdminUseCase(
        gateways=gateways,
        ledger=SimpleNamespace(list_recent=AsyncMock()),
    )
    payload = {
        "slug": "provider",
        "config": {"public_key": "***"},
        "contract_slug": "billing-contract",
    }

    result = await use_case.upsert_provider(payload=payload)

    assert result == {"provider": {"slug": "provider"}}
    args, kwargs = gateways.upsert.call_args
    sent = args[0]
    assert sent["config"]["linked_contract"] == "billing-contract"


@pytest.mark.asyncio
async def test_upsert_handles_invalid_config(caplog) -> None:
    gateways = SimpleNamespace(upsert=AsyncMock(return_value={"slug": "provider"}))
    use_case = ProvidersAdminUseCase(
        gateways=gateways,
        ledger=SimpleNamespace(list_recent=AsyncMock()),
    )

    await use_case.upsert_provider(
        payload={"slug": "provider", "config": "not-a-dict", "linked_contract": "c1"}
    )

    # Ensure a warning was emitted about invalid config
    assert any("Invalid provider config" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_delete_requires_slug() -> None:
    use_case = ProvidersAdminUseCase(
        gateways=SimpleNamespace(delete=AsyncMock()),
        ledger=SimpleNamespace(list_recent=AsyncMock()),
    )
    with pytest.raises(BillingUseCaseError):
        await use_case.delete_provider(slug="")


@pytest.mark.asyncio
async def test_list_transactions_uses_ledger() -> None:
    ledger = SimpleNamespace(list_recent=AsyncMock(return_value=[{"id": "txn"}]))
    use_case = ProvidersAdminUseCase(
        gateways=SimpleNamespace(),
        ledger=ledger,
    )

    result = await use_case.list_transactions(limit=5)

    assert result == {"items": [{"id": "txn"}]}
    ledger.list_recent.assert_awaited_once_with(limit=5)
