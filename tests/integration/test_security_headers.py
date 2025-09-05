from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.settings import EnvMode

os.environ["USE_MINIMAL_CONFIG"] = "True"


@pytest.mark.asyncio
async def test_cookie_security_flags(client: AsyncClient, test_user, monkeypatch) -> None:
    """Ensure cookies get hardened flags over HTTP without Secure."""
    monkeypatch.setattr(settings, "env_mode", EnvMode.production)
    login_data = {"username": "testuser", "password": "Password123"}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    cookies = response.headers.get_list("set-cookie")
    access_cookie = next(c for c in cookies if c.startswith("access_token="))
    assert "HttpOnly" in access_cookie
    assert "Secure" not in access_cookie
    assert "SameSite=Strict" in access_cookie


@pytest.mark.asyncio
async def test_csp_header(client: AsyncClient) -> None:
    response = await client.get("/", headers={"accept": "application/json"})
    assert response.status_code == 200
    csp = response.headers.get("content-security-policy")
    assert csp is not None
    directives = {d.strip().split(" ")[0]: d.strip() for d in csp.split(";") if d.strip()}
    script_src = directives.get("script-src")
    assert script_src == "script-src 'self'"
