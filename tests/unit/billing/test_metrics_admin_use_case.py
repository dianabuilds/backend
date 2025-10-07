from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.metrics import (
    MetricsAdminUseCase,
)


@pytest.mark.asyncio
async def test_summary_and_history_delegate_to_service() -> None:
    service = SimpleNamespace(
        get_summary_for_user=AsyncMock(return_value={"plan": None}),
        get_history_for_user=AsyncMock(return_value={"items": []}),
    )
    analytics = SimpleNamespace(
        kpi=AsyncMock(),
        subscription_metrics=AsyncMock(),
        revenue_timeseries=AsyncMock(return_value=[{"day": "2024-01-01"}]),
    )
    crypto = SimpleNamespace(
        get=AsyncMock(return_value=None), set=AsyncMock(return_value={"config": {}})
    )
    use_case = MetricsAdminUseCase(
        service=service, analytics=analytics, crypto_store=crypto
    )

    assert await use_case.summary(user_id="user") == {"plan": None}
    assert await use_case.history(user_id="user", limit=10) == {"items": []}
    service.get_summary_for_user.assert_awaited_once_with("user")
    service.get_history_for_user.assert_awaited_once_with("user", limit=10)


@pytest.mark.asyncio
async def test_kpi_metrics_revenue() -> None:
    service = SimpleNamespace(
        get_summary_for_user=AsyncMock(),
        get_history_for_user=AsyncMock(),
    )
    analytics = SimpleNamespace(
        kpi=AsyncMock(return_value={"success": 1}),
        subscription_metrics=AsyncMock(return_value={"active": 10}),
        revenue_timeseries=AsyncMock(
            return_value=[{"day": "2024-01-01", "amount": 1.0}]
        ),
    )
    crypto = SimpleNamespace(
        get=AsyncMock(return_value=None), set=AsyncMock(return_value={"config": {}})
    )
    use_case = MetricsAdminUseCase(
        service=service, analytics=analytics, crypto_store=crypto
    )

    assert await use_case.kpi() == {"success": 1}
    assert await use_case.metrics() == {"active": 10}
    assert await use_case.revenue_ts(days=14) == {
        "series": [{"day": "2024-01-01", "amount": 1.0}]
    }
    analytics.revenue_timeseries.assert_awaited_once_with(days=14)


@pytest.mark.asyncio
async def test_crypto_config_roundtrip() -> None:
    existing = {"config": {"rpc_endpoints": {"eth": "https://rpc"}, "retries": 1}}
    updated_row = {"config": {"rpc_endpoints": {"eth": "https://rpc"}, "retries": 2}}
    crypto = SimpleNamespace(
        get=AsyncMock(return_value=existing),
        set=AsyncMock(return_value=updated_row),
    )
    use_case = MetricsAdminUseCase(
        service=SimpleNamespace(
            get_summary_for_user=AsyncMock(), get_history_for_user=AsyncMock()
        ),
        analytics=SimpleNamespace(
            kpi=AsyncMock(),
            subscription_metrics=AsyncMock(),
            revenue_timeseries=AsyncMock(return_value=[]),
        ),
        crypto_store=crypto,
    )

    assert await use_case.get_crypto_config() == {"config": existing["config"]}
    result = await use_case.set_crypto_config(
        payload={
            "retries": 2,
            "gas_price_cap": "50",
            "fallback_networks": {"eth": "https://alt"},
        }
    )
    assert result == {"config": updated_row["config"]}
    crypto.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_crypto_config_defaults_to_empty() -> None:
    crypto = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
    use_case = MetricsAdminUseCase(
        service=SimpleNamespace(
            get_summary_for_user=AsyncMock(), get_history_for_user=AsyncMock()
        ),
        analytics=SimpleNamespace(
            kpi=AsyncMock(),
            subscription_metrics=AsyncMock(),
            revenue_timeseries=AsyncMock(return_value=[]),
        ),
        crypto_store=crypto,
    )

    assert await use_case.get_crypto_config() == {"config": {}}
