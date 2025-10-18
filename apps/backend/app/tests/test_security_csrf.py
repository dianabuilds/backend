from __future__ import annotations

from hashlib import sha256

import pytest
from fastapi import Depends, FastAPI, Response
from fastapi.testclient import TestClient

from domains.platform.iam.security import csrf_protect, issue_csrf_token
from packages.core.config import Settings


@pytest.fixture()
def csrf_client(monkeypatch):
    settings = Settings(
        env="prod",
        auth_csrf_cookie_name="TEST-CSRF",
        auth_csrf_header_name="X-Test-CSRF",
        admin_api_key="admin-secret",
    )
    monkeypatch.setattr("domains.platform.iam.security.load_settings", lambda: settings)

    app = FastAPI()

    @app.post("/protected", dependencies=[Depends(csrf_protect)])
    async def protected() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    return client, settings


def test_csrf_rejects_missing_header(csrf_client):
    client, _ = csrf_client
    response = client.post("/protected")
    assert response.status_code == 403
    assert response.json()["detail"] == "csrf_failed"


def test_csrf_rejects_mismatched_header(csrf_client):
    client, settings = csrf_client
    client.cookies.set(settings.auth_csrf_cookie_name, "token-a")
    response = client.post(
        "/protected",
        headers={settings.auth_csrf_header_name: "token-b"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "csrf_failed"


def test_csrf_allows_matching_cookie_header(csrf_client):
    client, settings = csrf_client
    token = "token-123"
    client.cookies.set(settings.auth_csrf_cookie_name, token)
    response = client.post(
        "/protected",
        headers={settings.auth_csrf_header_name: token},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_csrf_admin_key_bypass(csrf_client):
    client, settings = csrf_client
    admin_key = (
        settings.admin_api_key.get_secret_value() if settings.admin_api_key else ""
    )
    response = client.post(
        "/protected",
        headers={"X-Admin-Key": admin_key},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_issue_csrf_token_sets_cookie_and_header():
    settings = Settings(
        env="dev",
        auth_csrf_cookie_name="CSRF",
        auth_csrf_header_name="X-CSRF",
        auth_csrf_ttl_seconds=480,
    )
    response = Response()
    token, ttl = issue_csrf_token(response, settings)

    assert ttl == 480
    assert response.headers[settings.auth_csrf_header_name] == token
    cookies = response.headers.get("set-cookie", "")
    assert settings.auth_csrf_cookie_name in cookies
    assert sha256(token.encode()).hexdigest()
