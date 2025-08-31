import importlib
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Ensure app package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.search.api.admin_router import admin_required
from app.domains.search.api.admin_router import router as admin_router
from app.domains.search.application.stats_service import search_stats


@pytest.mark.asyncio
async def test_admin_search_top_endpoint():
    search_stats.reset()
    search_stats.record("foo", 2)
    search_stats.record("foo", 4)
    search_stats.record("bar", 0)

    app = FastAPI()
    app.include_router(admin_router)
    app.dependency_overrides[admin_required] = lambda: None

    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        res = await ac.get("/admin/search/top")
    assert res.status_code == 200
    data = res.json()
    assert data[0]["query"] == "foo"
    assert data[0]["count"] == 2
    assert data[0]["results"] == 4
    assert any(item["query"] == "bar" and item["results"] == 0 for item in data)
