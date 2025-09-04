import importlib
import sys

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.search.api.admin_router import admin_required  # noqa: E402
from app.domains.search.api.admin_router import router as admin_router  # noqa: E402
from app.domains.search.application.stats_service import search_stats  # noqa: E402


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
