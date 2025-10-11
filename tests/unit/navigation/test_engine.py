from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from domains.product.navigation.infrastructure import engine as engine_module


class DummySQLAlchemyError(SQLAlchemyError):
    pass


@pytest.mark.asyncio
async def test_ensure_engine_builds_async_engine(monkeypatch):
    container = SimpleNamespace(settings=SimpleNamespace(database_url="postgres://db"))

    calls: dict[str, Any] = {}

    def fake_to_async_dsn(url: str) -> str:
        calls["to_async_dsn"] = url
        return "postgresql+asyncpg://db?sslmode=disable"

    def fake_get_async_engine(label: str, *, url: str, future: bool):
        calls["get_async_engine"] = (label, url, future)
        return object()

    monkeypatch.setattr(engine_module, "to_async_dsn", fake_to_async_dsn)
    monkeypatch.setattr(engine_module, "get_async_engine", fake_get_async_engine)

    result = await engine_module.ensure_engine(container, label="nav")

    assert calls["to_async_dsn"] == "postgres://db"
    assert calls["get_async_engine"] == ("nav", "postgresql+asyncpg://db", True)
    assert result is not None


@pytest.mark.asyncio
async def test_ensure_engine_returns_none_when_dsn_missing(monkeypatch):
    container = SimpleNamespace(settings=SimpleNamespace(database_url="postgres://db"))

    monkeypatch.setattr(engine_module, "to_async_dsn", lambda url: "")

    result = await engine_module.ensure_engine(container)

    assert result is None


@pytest.mark.asyncio
async def test_ensure_engine_handles_invalid_config(monkeypatch, caplog):
    container = SimpleNamespace(settings=SimpleNamespace(database_url="postgres://db"))

    def fake_to_async_dsn(url: str) -> str:
        raise ValueError("invalid")

    monkeypatch.setattr(engine_module, "to_async_dsn", fake_to_async_dsn)

    result = await engine_module.ensure_engine(container)

    assert result is None
    assert any("invalid" in message for message in caplog.messages)


@pytest.mark.asyncio
async def test_ensure_engine_handles_sqlalchemy_error(monkeypatch, caplog):
    container = SimpleNamespace(settings=SimpleNamespace(database_url="postgres://db"))

    monkeypatch.setattr(
        engine_module, "to_async_dsn", lambda url: "postgresql+asyncpg://db"
    )

    def fake_get_async_engine(label: str, *, url: str, future: bool):
        raise DummySQLAlchemyError("boom")

    monkeypatch.setattr(engine_module, "get_async_engine", fake_get_async_engine)

    result = await engine_module.ensure_engine(container)

    assert result is None
    assert any("failed to create engine" in message for message in caplog.messages)
