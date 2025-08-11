import pytest
from httpx import AsyncClient

from app.services.navcache import navcache
from app.core.log_events import cache_counters, cache_key_hits
from app.core.config import settings
from app.core.rate_limit import recent_429
from app.models.user import User


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_cache_stats_and_invalidate(client: AsyncClient, admin_user: User, moderator_user: User):
    cache_counters.clear()
    cache_key_hits.clear()
    await navcache.set_navigation("u1", "n1", "auto", {"a": 1}, ttl_sec=60)
    await navcache.get_navigation("u1", "n1", "auto")
    await navcache.get_navigation("u1", "n2", "auto")
    headers_mod = await login(client, "moderator")
    resp = await client.get("/admin/cache/stats", headers=headers_mod)
    assert resp.status_code == 200
    data = resp.json()
    assert data["counters"]["nav"]["hit"] >= 1
    assert data["counters"]["nav"]["miss"] >= 1
    assert data["hot_keys"][0]["ttl"] > 0
    pattern = f"{settings.cache.key_version}:nav*"
    resp = await client.post(
        "/admin/cache/invalidate_by_pattern",
        headers=headers_mod,
        json={"pattern": pattern},
    )
    assert resp.status_code == 403
    headers_admin = await login(client, "admin")
    resp = await client.post(
        "/admin/cache/invalidate_by_pattern",
        headers=headers_admin,
        json={"pattern": pattern},
    )
    assert resp.status_code == 200
    assert await navcache.get_navigation("u1", "n1", "auto") is None


@pytest.mark.asyncio
async def test_ratelimit_endpoints(client: AsyncClient, admin_user: User, moderator_user: User):
    headers_mod = await login(client, "moderator")
    headers_admin = await login(client, "admin")
    resp = await client.get("/admin/ratelimit/rules", headers=headers_mod)
    assert resp.status_code == 200
    recent_429.clear()
    recent_429.append({"path": "/x", "ip": "127.0.0.1", "rule": "1/s", "ts": "now"})
    resp = await client.get("/admin/ratelimit/recent429", headers=headers_mod)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    prev = settings.rate_limit.enabled
    try:
        settings.rate_limit.enabled = True
        resp = await client.post(
            "/admin/ratelimit/disable",
            headers=headers_mod,
            json={"disabled": True},
        )
        assert resp.status_code == 403
        resp = await client.post(
            "/admin/ratelimit/disable",
            headers=headers_admin,
            json={"disabled": True},
        )
        assert resp.status_code == 200
        assert settings.rate_limit.enabled is False
    finally:
        settings.rate_limit.enabled = prev
