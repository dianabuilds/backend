from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from apps.backendDDD.app.api_gateway.main import app
from apps.backendDDD.packages.core.config import load_settings


def _user_token(sub: str = "u1", role: str = "user") -> str:
    s = load_settings()
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    return jwt.encode(payload, key=s.auth_jwt_secret, algorithm=s.auth_jwt_algorithm)


def _set_auth(client: TestClient, token: str) -> None:
    s = load_settings()
    client.cookies.set("access_token", token)
    client.cookies.set(s.auth_csrf_cookie_name, "t1")


@pytest.mark.asyncio
async def test_nodes_crud_and_tags():
    token = _user_token("author-1")
    headers = {load_settings().auth_csrf_header_name: "t1"}
    with TestClient(app) as client:
        _set_auth(client, token)
        # Create
        r = client.post(
            "/v1/nodes",
            json={"title": "First", "tags": ["Python"], "is_public": True},
            headers=headers,
        )
        assert r.status_code == 200, r.text
        nid = r.json()["id"]

        # Get
        r = client.get(f"/v1/nodes/{nid}")
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "First"
        assert "python" in [t.lower() for t in body["tags"]]

        # Patch
        r = client.patch(f"/v1/nodes/{nid}", json={"title": "Updated"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

        # Set tags
        r = client.put(
            f"/v1/nodes/{nid}/tags", json={"tags": ["ai", "ml"]}, headers=headers
        )
        assert r.status_code == 200
        assert set(r.json()["tags"]) == {"ai", "ml"}

        # Delete
        r = client.delete(f"/v1/nodes/{nid}", headers=headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
