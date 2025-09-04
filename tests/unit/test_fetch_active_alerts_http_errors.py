import logging
import os

import httpx
import pytest

from app.admin.ops.alerts import fetch_active_alerts


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [405, 422, 500])
async def test_fetch_active_alerts_http_errors(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    status_code: int,
) -> None:
    os.environ["PROMETHEUS_URL"] = "http://prom"

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - helper
        return httpx.Response(status_code, json={})

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: original_client(*args, transport=transport, **kwargs),
    )

    with caplog.at_level(logging.WARNING):
        alerts = await fetch_active_alerts()

    assert alerts == []
    assert any(str(status_code) in record.getMessage() for record in caplog.records)
