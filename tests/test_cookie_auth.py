import pytest


@pytest.mark.asyncio
async def test_login_sets_cookies(client, test_user):
    resp = await client.post(
        "/auth/login", json={"username": "testuser", "password": "Password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies
    csrf = body["csrf_token"]

    # Logout without CSRF should fail
    fail = await client.post("/auth/logout")
    assert fail.status_code == 403

    # Logout with CSRF token
    ok = await client.post("/auth/logout", headers={"X-CSRF-Token": csrf})
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_refresh_rotates_token(client, test_user):
    resp = await client.post(
        "/auth/login", json={"username": "testuser", "password": "Password123"}
    )
    assert resp.status_code == 200
    old_refresh = resp.cookies.get("refresh_token")

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    new_refresh = refresh_resp.cookies.get("refresh_token")
    assert new_refresh and new_refresh != old_refresh

    # old refresh token should be invalid now
    client.cookies.set("refresh_token", old_refresh)
    invalid = await client.post("/auth/refresh")
    assert invalid.status_code == 401

