from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api_gateway.main import app
from packages.core.config import load_settings


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
        r = client.put(f"/v1/nodes/{nid}/tags", json={"tags": ["ai", "ml"]}, headers=headers)
        assert r.status_code == 200
        assert set(r.json()["tags"]) == {"ai", "ml"}

        # Delete
        r = client.delete(f"/v1/nodes/{nid}", headers=headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_admin_node_moderation_decision_flow():
    token = _user_token("moderation-author", role="user")
    headers = {load_settings().auth_csrf_header_name: "t1"}
    admin_headers = {"X-Admin-Key": "adminkey"}
    with TestClient(app) as client:
        _set_auth(client, token)
        create = client.post(
            "/v1/nodes",
            json={"title": "Needs review", "tags": ["alpha"], "is_public": True},
            headers=headers,
        )
        assert create.status_code == 200, create.text
        node_id = create.json()["id"]

        detail_before = client.get(f"/v1/admin/nodes/{node_id}/moderation", headers=admin_headers)
        assert detail_before.status_code == 200, detail_before.text
        assert detail_before.json()["status"] == "pending"

        decision = client.post(
            f"/v1/admin/nodes/{node_id}/moderation/decision",
            json={"action": "hide", "reason": "spam"},
            headers=admin_headers,
        )
        assert decision.status_code == 200, decision.text
        body = decision.json()
        assert body.get("status") == "hidden"

        detail_after = client.get(f"/v1/admin/nodes/{node_id}/moderation", headers=admin_headers)
        assert detail_after.status_code == 200, detail_after.text
        data = detail_after.json()
        assert data["status"] == "hidden"
        history = data.get("moderation_history") or []
        assert history and history[0].get("action") == "hide"

        listing = client.get("/v1/admin/nodes/list", headers=admin_headers)
        assert listing.status_code == 200, listing.text
        entries = listing.json()
        match = next((item for item in entries if item.get("id") == str(node_id)), None)
        assert match is not None
        assert match.get("moderation_status") == "hidden"
        assert match.get("moderation_status_updated_at")
