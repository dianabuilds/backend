from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.core.metrics import metrics_storage
from app.core.metrics_middleware import MetricsMiddleware


@pytest.mark.asyncio
async def test_account_from_query() -> None:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/q")
    async def _q() -> dict[str, str]:
        return {"status": "ok"}

    metrics_storage.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/q", params={"account_id": "acc1"})
    summary = metrics_storage.summary(3600, account_id="acc1")
    assert summary["count"] == 1


@pytest.mark.asyncio
async def test_account_from_state() -> None:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/s")
    async def _s(request: Request) -> dict[str, str]:
        request.state.account_id = "acc2"
        return {"status": "ok"}

    metrics_storage.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/s")
    summary = metrics_storage.summary(3600, account_id="acc2")
    assert summary["count"] == 1


@pytest.mark.asyncio
async def test_account_from_path() -> None:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/p/{account_id}")
    async def _p(account_id: str) -> dict[str, str]:
        return {"status": account_id}

    metrics_storage.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/p/acc3")
    summary = metrics_storage.summary(3600, account_id="acc3")
    assert summary["count"] == 1
