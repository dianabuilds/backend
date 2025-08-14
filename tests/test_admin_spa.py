import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_admin_spa_placeholder(client):
    resp = await client.get("/admin")
    assert resp.status_code == 200
    assert "Admin SPA build not found" in resp.text


@pytest.mark.asyncio
async def test_admin_spa_serves_index_and_fallback(client, monkeypatch):
    dist_dir = Path(__file__).resolve().parent.parent / "admin-frontend" / "dist"
    index_file = dist_dir / "index.html"
    dist_dir.mkdir(parents=True, exist_ok=True)
    index_file.write_text("<h1>Admin SPA</h1>")

    monkeypatch.setenv("TESTING", "False")

    resp = await client.get("/admin")
    assert resp.status_code == 200
    assert "Admin SPA" in resp.text

    resp = await client.get("/admin/some/route")
    assert resp.status_code == 200
    assert "Admin SPA" in resp.text


@pytest.mark.asyncio
async def test_admin_assets_cache_headers(client, monkeypatch):
    dist_dir = Path(__file__).resolve().parent.parent / "admin-frontend" / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("index")
    asset_file = assets_dir / "app.js"
    asset_file.write_text("console.log('hi')")

    from app.main import app
    from app.web.immutable_static import ImmutableStaticFiles

    app.mount("/admin/assets", ImmutableStaticFiles(directory=assets_dir), name="admin-assets-test")

    monkeypatch.setenv("TESTING", "False")

    resp = await client.get("/admin/assets/app.js")
    assert resp.status_code == 200
    cache = resp.headers.get("Cache-Control")
    assert cache and "immutable" in cache and "max-age" in cache
