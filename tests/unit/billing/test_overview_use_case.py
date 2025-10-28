from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.overview import (
    OverviewUseCases,
)
from apps.backend.domains.platform.billing.application.use_cases.metrics import (
    MetricsAdminUseCase,
)


@pytest.mark.asyncio
async def test_dashboard_combines_metrics() -> None:
    metrics = SimpleNamespace(
        kpi=AsyncMock(return_value={"success": 10}),
        metrics=AsyncMock(return_value={"active_subs": 5}),
        revenue_ts=AsyncMock(return_value={"series": [1, 2]}),
        network_breakdown=AsyncMock(return_value={"networks": []}),
        summary=AsyncMock(),
        history=AsyncMock(),
        get_crypto_config=AsyncMock(),
        set_crypto_config=AsyncMock(),
    )
    ledger = SimpleNamespace(
        list_recent=AsyncMock(return_value=[{"status": "pending"}])
    )
    service = SimpleNamespace()

    use_case = OverviewUseCases(
        metrics=cast(MetricsAdminUseCase, metrics), ledger=ledger, service=service
    )
    result = await use_case.dashboard()

    assert result == {
        "kpi": {"success": 10},
        "subscriptions": {"active_subs": 5},
        "revenue": [1, 2],
    }
    metrics.kpi.assert_awaited_once()
    metrics.metrics.assert_awaited_once()
    metrics.revenue_ts.assert_awaited_once()


@pytest.mark.asyncio
async def test_payouts_filters_successful() -> None:
    metrics = SimpleNamespace(
        kpi=AsyncMock(),
        metrics=AsyncMock(),
        revenue_ts=AsyncMock(),
        network_breakdown=AsyncMock(return_value={"networks": []}),
        summary=AsyncMock(),
        history=AsyncMock(),
        get_crypto_config=AsyncMock(),
        set_crypto_config=AsyncMock(),
    )
    ledger = SimpleNamespace(
        list_recent=AsyncMock(
            return_value=[
                {"status": "succeeded"},
                {"status": "pending"},
                {"status": "failed"},
            ]
        )
    )
    service = SimpleNamespace()

    use_case = OverviewUseCases(
        metrics=cast(MetricsAdminUseCase, metrics), ledger=ledger, service=service
    )
    result = await use_case.payouts(limit=10)

    assert result == {"items": [{"status": "pending"}, {"status": "failed"}]}
    ledger.list_recent.assert_awaited_once()
