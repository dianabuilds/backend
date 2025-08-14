import asyncio
import json
import logging

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.console_access_log import ConsoleAccessLogMiddleware
from app.core.log_filters import request_id_var, user_id_var
from app.services.navcache import NavCache
from app.services.cache_backends import MemoryCache


@pytest.mark.asyncio
async def test_logging_middleware_basic(client):
    logger = logging.getLogger("app.http")
    records: list[str] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - simple
            records.append(record.getMessage())

    handler = ListHandler()
    logger.addHandler(handler)
    try:
        resp = await client.get("/health")
    finally:
        logger.removeHandler(handler)

    assert resp.status_code == 200
    assert "X-Request-Id" in resp.headers
    assert any("GET /health 200" in r for r in records)


@pytest.mark.asyncio
async def test_console_access_log_middleware(capsys):
    app = FastAPI()
    app.add_middleware(ConsoleAccessLogMiddleware)

    @app.get("/ping")
    async def _ping():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/ping")
    out = capsys.readouterr().out
    assert "HTTP GET /ping -> 200" in out


@pytest.mark.asyncio
async def test_logging_cache_events(caplog):
    nc = NavCache(MemoryCache())
    with caplog.at_level(logging.INFO):
        assert await nc.get_navigation("u", "s", None) is None
        await nc.set_navigation("u", "s", None, {"ok": True})
        assert await nc.get_navigation("u", "s", None) is not None
        await nc.invalidate_navigation_by_user("u")
    text = caplog.text
    assert "CACHE_MISS" in text
    assert "CACHE_HIT" in text
    assert "CACHE_INVALIDATE" in text


@pytest.mark.asyncio
async def test_json_formatter(capsys):
    prev = settings.logging.json
    try:
        settings.logging.json = True
        configure_logging()
        request_id_var.set("rid")
        user_id_var.set("uid")
        logging.getLogger("app").info("hello")
        line = capsys.readouterr().out.strip().splitlines()[-1]
        data = json.loads(line)
        assert data["request_id"] == "rid"
        assert data["user_id"] == "uid"
        assert data["service"] == settings.logging.service_name
    finally:
        settings.logging.json = prev
        configure_logging()


@pytest.mark.asyncio
async def test_slow_request_threshold(capsys):
    prev = settings.logging.slow_request_ms
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/slow")
    async def _slow():
        await asyncio.sleep(0.01)
        return {"ok": True}

    try:
        settings.logging.slow_request_ms = 1
        configure_logging()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/slow")
        out = capsys.readouterr().out
        assert "GET /slow 200" in out
        assert "WARNING" in out
    finally:
        settings.logging.slow_request_ms = prev
        configure_logging()


def test_uvicorn_integration(capsys):
    configure_logging()
    configure_logging()
    logging.getLogger("uvicorn").info("ping")
    assert "ping" in capsys.readouterr().out

