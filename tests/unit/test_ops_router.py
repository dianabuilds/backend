import asyncio
import importlib
import os
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

os.environ.setdefault("TESTING", "True")
os.environ["BUILD_VERSION"] = "123"

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.api import ops as ops_module  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from app.admin.ops import alerts as alerts_module  # noqa: E402
from app.core.cache import cache as shared_cache  # noqa: E402

app = FastAPI()
app.include_router(ops_module.router)


async def _admin_dep():
    return SimpleNamespace(id="admin", role="admin")


app.dependency_overrides[ops_module.admin_required] = _admin_dep

client = TestClient(app)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def clear_ops_cache():
    async def _clear():
        keys = await shared_cache.scan("ops:*")
        if keys:
            await shared_cache.delete(*keys)

    run(_clear())


def test_status_endpoint_cached():
    clear_ops_cache()
    workspace_id = uuid4()
    calls = {"n": 0}

    async def fake_readyz(db):  # pragma: no cover - helper
        calls["n"] += 1
        return JSONResponse({"ready": "ok"})

    async def fake_get(db, ws_id):  # pragma: no cover - helper
        return SimpleNamespace(
            id=ws_id, slug="demo", name="Demo", settings_json={"limits": {}}
        )

    ops_module.readyz = fake_readyz
    ops_module.WorkspaceDAO.get = fake_get

    resp1 = client.get(f"/admin/ops/status?workspace_id={workspace_id}")
    assert resp1.status_code == 200
    data = resp1.json()
    assert data["build"] == "123"
    assert data["workspace"]["slug"] == "demo"
    assert data["ready"]["ready"] == "ok"

    resp2 = client.get(f"/admin/ops/status?workspace_id={workspace_id}")
    assert resp2.json() == data
    assert calls["n"] == 1


def test_limits_endpoint_remaining_and_cached():
    clear_ops_cache()
    workspace_id = uuid4()

    async def fake_get(db, ws_id):  # pragma: no cover - helper
        return SimpleNamespace(
            id=ws_id,
            slug="demo",
            name="Demo",
            settings_json={
                "limits": {"ai_tokens": 100, "notif_per_day": 10, "compass_calls": 5}
            },
        )

    ops_module.WorkspaceDAO.get = fake_get

    now = datetime.now(UTC)
    period = now.strftime("%Y%m%d")

    async def setup():  # pragma: no cover - helper
        await shared_cache.incr(f"q:ai_tokens:{period}:user1:{workspace_id}", 40)
        await shared_cache.incr(f"q:notif_per_day:{period}:user1:{workspace_id}", 3)

    run(setup())

    resp1 = client.get(f"/admin/ops/limits?workspace_id={workspace_id}")
    assert resp1.status_code == 200
    data = resp1.json()
    assert data["ai_tokens"] == 60
    assert data["notif_per_day"] == 7
    assert data["compass_calls"] == 5

    async def more():  # pragma: no cover - helper
        await shared_cache.incr(f"q:ai_tokens:{period}:user1:{workspace_id}", 10)

    run(more())

    resp2 = client.get(f"/admin/ops/limits?workspace_id={workspace_id}")
    assert resp2.json() == data


def test_alerts_endpoint(monkeypatch):
    async def fake_fetch():  # pragma: no cover - helper
        return [{"id": "1", "description": "boom"}]

    monkeypatch.setattr(alerts_module, "fetch_active_alerts", fake_fetch)

    resp = client.get("/admin/ops/alerts")
    assert resp.status_code == 200
    assert resp.json()["alerts"][0]["description"] == "boom"
