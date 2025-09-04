from __future__ import annotations

import asyncio
import importlib
import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("TESTING", "True")
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.api import health as health_module  # noqa: E402
from app.core.cache import cache as shared_cache  # noqa: E402
from app.core.db.session import get_db  # noqa: E402

app = FastAPI()
app.include_router(health_module.router)


async def _fake_db():
    yield object()


app.dependency_overrides[get_db] = _fake_db

client = TestClient(app)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def clear_readyz_cache() -> None:
    run(shared_cache.delete("ops:readyz"))


def test_readyz_cached(monkeypatch) -> None:
    clear_readyz_cache()
    calls = {"n": 0}

    async def fake_db_check(session):
        calls["n"] += 1
        return True

    async def _ok(*args, **kwargs):  # pragma: no cover - helper
        return True

    monkeypatch.setattr(health_module, "_check_db", fake_db_check)
    monkeypatch.setattr(health_module, "_check_redis", _ok)
    monkeypatch.setattr(health_module, "_check_queue", _ok)
    monkeypatch.setattr(health_module, "_check_ai_service", _ok)
    monkeypatch.setattr(health_module, "_check_payment_service", _ok)

    resp1 = client.get("/readyz")
    assert resp1.status_code == 200
    resp2 = client.get("/readyz")
    assert resp2.status_code == 200
    assert calls["n"] == 1
