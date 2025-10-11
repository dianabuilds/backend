from __future__ import annotations

from types import SimpleNamespace
from hashlib import sha256

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from apps.backend.app.api_gateway import debug


@pytest.fixture()
def app(monkeypatch):
    def _build(settings: SimpleNamespace, current_user: AsyncMock | None = None):
        monkeypatch.setattr(debug, "load_settings", lambda: settings)
        if current_user is not None:
            monkeypatch.setattr(debug, "get_current_user", current_user)
        else:
            monkeypatch.setattr(
                debug, "get_current_user", AsyncMock(return_value={"sub": "42"})
            )
        router = debug.make_router()
        application = FastAPI()
        application.include_router(router)
        return application

    return _build


def test_debug_config_exposes_safe_settings(app):
    settings = SimpleNamespace(
        env="test",
        auth_jwt_algorithm="HS256",
        auth_jwt_secret="super-secret",
        admin_api_key="admin-key",
    )
    application = app(settings)
    client = TestClient(application)

    response = client.get("/debug/config")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "env": "test",
        "jwt_algorithm": "HS256",
        "jwt_secret_hint": sha256(b"super-secret").hexdigest()[:10],
        "admin_key_present": True,
        "admin_key_len": len("admin-key"),
    }


def test_debug_whoami_returns_claims_and_admin_match(app):
    settings = SimpleNamespace(
        env="dev",
        auth_jwt_algorithm="HS256",
        auth_jwt_secret="secret",
        admin_api_key="key-123",
    )
    current_user = AsyncMock(return_value={"sub": "user-1", "role": "admin"})
    application = app(settings, current_user=current_user)
    client = TestClient(application)

    response = client.get("/debug/whoami", headers={"X-Admin-Key": "key-123"})

    assert response.status_code == 200
    data = response.json()
    assert data["env"] == "dev"
    assert data["claims"] == {"sub": "user-1", "role": "admin"}
    assert data["admin_key_present"] is True
    assert data["admin_key_match"] is True
    current_user.assert_awaited_once()


def test_debug_whoami_handles_auth_errors(app):
    settings = SimpleNamespace(
        env="dev",
        auth_jwt_algorithm="HS384",
        auth_jwt_secret="secret",
        admin_api_key="key-123",
    )
    current_user = AsyncMock(side_effect=RuntimeError("boom"))
    application = app(settings, current_user=current_user)
    client = TestClient(application)

    response = client.get("/debug/whoami", headers={"X-Admin-Key": "mismatch"})

    assert response.status_code == 200
    data = response.json()
    assert data["claims"] == {"error": "boom"}
    assert data["admin_key_present"] is True
    assert data["admin_key_match"] is False
    current_user.assert_awaited()
