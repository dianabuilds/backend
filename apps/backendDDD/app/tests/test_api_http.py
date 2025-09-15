from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from apps.backendDDD.app.api_gateway.main import app
from apps.backendDDD.packages.core.config import load_settings


def _admin_token(sub: str = "u1") -> str:
    s = load_settings()
    payload = {"sub": sub, "role": "admin", "exp": int(time.time()) + 600}
    return jwt.encode(payload, key=s.auth_jwt_secret, algorithm=s.auth_jwt_algorithm)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _with_csrf(headers: dict[str, str] | None = None) -> dict[str, str]:
    s = load_settings()
    csrf_header = s.auth_csrf_header_name
    token = "t1"
    h = {csrf_header: token}
    if headers:
        h.update(headers)
    return h


def test_notifications_send_admin(client: TestClient):
    token = _admin_token()
    s = load_settings()
    cookies = {"access_token": token, s.auth_csrf_cookie_name: "t1"}
    r = client.post(
        "/v1/notifications/send",
        json={"channel": "log", "payload": {"msg": "hi"}},
        headers=_with_csrf(),
        cookies=cookies,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


def test_profile_update_username_owner(client: TestClient):
    user_id = "u99"
    token = _admin_token(sub=user_id)  # owner token
    s = load_settings()
    cookies = {"access_token": token, s.auth_csrf_cookie_name: "t1"}
    r = client.put(
        f"/v1/profile/{user_id}/username",
        json={"username": "neo"},
        headers=_with_csrf(),
        cookies=cookies,
    )
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "neo"
