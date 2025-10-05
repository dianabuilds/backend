from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api_gateway.main import app
from packages.core.config import load_settings


def _user_token(sub: str = "u2", role: str = "user") -> str:
    s = load_settings()
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    return jwt.encode(payload, key=s.auth_jwt_secret, algorithm=s.auth_jwt_algorithm)


def _set_auth(client: TestClient, token: str) -> None:
    s = load_settings()
    client.cookies.set("access_token", token)
    client.cookies.set(s.auth_csrf_cookie_name, "t1")


@pytest.mark.asyncio
async def test_quests_create_get_tags_patch():
    token = _user_token("author-2")
    headers = {load_settings().auth_csrf_header_name: "t1"}
    with TestClient(app) as client:
        _set_auth(client, token)
        # Create
        r = client.post(
            "/v1/quests",
            json={
                "title": "Quest 1",
                "description": "d",
                "tags": ["rpg"],
                "is_public": True,
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text
        qid = r.json()["id"]

        # Get
        r = client.get(f"/v1/quests/{qid}")
        assert r.status_code == 200
        j = r.json()
        assert j["title"] == "Quest 1"

        # Set tags
        r = client.put(
            f"/v1/quests/{qid}/tags", json={"tags": ["story"]}, headers=headers
        )
        assert r.status_code == 200
        assert r.json()["tags"] == ["story"]
