from __future__ import annotations

import time
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.api_gateway.main import app
from packages.core.config import load_settings


def _admin_token(sub: str = "admin-user") -> str:
    s = load_settings()
    payload = {"sub": sub, "role": "admin", "exp": int(time.time()) + 600}
    return jwt.encode(
        payload,
        key=s.auth_jwt_secret.get_secret_value(),
        algorithm=s.auth_jwt_algorithm,
    )


def _user_token(sub: str) -> str:
    s = load_settings()
    payload = {"sub": sub, "role": "user", "exp": int(time.time()) + 600}
    return jwt.encode(
        payload,
        key=s.auth_jwt_secret.get_secret_value(),
        algorithm=s.auth_jwt_algorithm,
    )


def _with_csrf(headers: dict[str, str] | None = None) -> dict[str, str]:
    s = load_settings()
    csrf_header = s.auth_csrf_header_name
    token = "t1"
    h = {csrf_header: token}
    if headers:
        h.update(headers)
    return h


@pytest.mark.asyncio
async def test_achievements_crud_and_grants():
    admin_tok = _admin_token()
    user_id = str(uuid4())
    user_tok = _user_token(user_id)
    s = load_settings()
    with TestClient(app) as client:
        # set cookies for admin and csrf
        client.cookies.set("access_token", admin_tok)
        client.cookies.set(s.auth_csrf_cookie_name, "t1")

        # list admin empty
        r0 = client.get("/v1/admin/achievements", headers=_with_csrf())
        assert r0.status_code == 200, r0.text

        # create
        code = f"code-{uuid4().hex[:6]}"
        c = client.post(
            "/v1/admin/achievements",
            json={
                "code": code,
                "title": "First",
                "description": "desc",
                "visible": True,
                "condition": {"t": 1},
            },
            headers=_with_csrf(),
        )
        assert c.status_code == 200, c.text
        ach_id = c.json()["id"]

        # conflict on duplicate code
        dup = client.post(
            "/v1/admin/achievements",
            json={"code": code, "title": "dup"},
            headers=_with_csrf(),
        )
        assert dup.status_code == 409, dup.text

        # update
        u = client.patch(
            f"/v1/admin/achievements/{ach_id}",
            json={"title": "Updated"},
            headers=_with_csrf(),
        )
        assert u.status_code == 200, u.text
        assert u.json()["title"] == "Updated"

        # grant to user
        g = client.post(
            f"/v1/admin/achievements/{ach_id}/grant",
            json={"user_id": user_id},
            headers=_with_csrf(),
        )
        assert g.status_code == 200, g.text
        assert g.json()["granted"] is True

        # user lists -> unlocked
        client.cookies.set("access_token", user_tok)
        # no need to set csrf for GET
        lu = client.get("/v1/achievements")
        assert lu.status_code == 200, lu.text
        items = lu.json()
        assert any(it["id"] == ach_id and it["unlocked"] for it in items)

        # revoke
        client.cookies.set("access_token", admin_tok)
        rv = client.post(
            f"/v1/admin/achievements/{ach_id}/revoke",
            json={"user_id": user_id},
            headers=_with_csrf(),
        )
        assert rv.status_code == 200, rv.text
        assert rv.json()["revoked"] is True

        # user lists -> locked now
        client.cookies.set("access_token", user_tok)
        lu2 = client.get("/v1/achievements")
        assert lu2.status_code == 200, lu2.text
        items2 = lu2.json()
        assert any(it["id"] == ach_id and not it["unlocked"] for it in items2)

        # delete achievement
        client.cookies.set("access_token", admin_tok)
        d = client.delete(f"/v1/admin/achievements/{ach_id}", headers=_with_csrf())
        assert d.status_code == 200, d.text
        assert d.json()["ok"] is True
