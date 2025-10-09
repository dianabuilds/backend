from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.api_gateway.main import app
from packages.core.config import load_settings

ADMIN_KEY = str(load_settings().admin_api_key or "")
if not ADMIN_KEY:
    pytest.skip(
        "APP_ADMIN_API_KEY is required for admin endpoints", allow_module_level=True
    )


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


@pytest.mark.asyncio
async def test_admin_node_moderation_decision_flow():
    token = _user_token("moderation-author", role="user")
    headers = {load_settings().auth_csrf_header_name: "t1"}
    admin_headers = {"X-Admin-Key": ADMIN_KEY}
    with TestClient(app) as client:
        _set_auth(client, token)
        create = client.post(
            "/v1/nodes",
            json={"title": "Needs review", "tags": ["alpha"], "is_public": True},
            headers=headers,
        )
        assert create.status_code == 200, create.text
        node_id = create.json()["id"]

        detail_before = client.get(
            f"/v1/admin/nodes/{node_id}/moderation", headers=admin_headers
        )
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

        detail_after = client.get(
            f"/v1/admin/nodes/{node_id}/moderation", headers=admin_headers
        )
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


@pytest.mark.asyncio
async def test_node_engagement_endpoints():
    token = _user_token("engagement-author")
    headers = {load_settings().auth_csrf_header_name: "t1"}
    with TestClient(app) as client:
        _set_auth(client, token)
        create = client.post(
            "/v1/nodes",
            json={"title": "Engagement", "tags": ["demo"], "is_public": True},
            headers=headers,
        )
        assert create.status_code == 200, create.text
        node_id = create.json()["id"]

        view_resp = client.post(
            f"/v1/nodes/{node_id}/views",
            json={"amount": 1, "fingerprint": "fp-demo"},
            headers=headers,
        )
        assert view_resp.status_code == 200, view_resp.text
        assert view_resp.json()["views_count"] >= 1

        views_summary = client.get(f"/v1/nodes/{node_id}/views")
        assert views_summary.status_code == 200
        summary_body = views_summary.json()
        assert summary_body["total"] >= 1
        assert isinstance(summary_body["buckets"], list)

        like = client.post(f"/v1/nodes/{node_id}/reactions/like", headers=headers)
        assert like.status_code == 200
        assert like.json()["liked"] is True

        reactions = client.get(f"/v1/nodes/{node_id}/reactions")
        assert reactions.status_code == 200
        assert reactions.json()["totals"].get("like", 0) >= 1

        unlike = client.delete(f"/v1/nodes/{node_id}/reactions/like", headers=headers)
        assert unlike.status_code == 200
        assert unlike.json()["liked"] is False

        comment = client.post(
            f"/v1/nodes/{node_id}/comments",
            json={"content": "First!"},
            headers=headers,
        )
        assert comment.status_code == 200, comment.text
        comment_id = comment.json()["id"]

        admin_headers = {
            "X-Admin-Key": ADMIN_KEY,
            "X-Actor-Id": "00000000-0000-0000-0000-000000000001",
        }

        engagement_admin = client.get(
            f"/v1/admin/nodes/{node_id}/engagement",
            headers=admin_headers,
        )
        assert engagement_admin.status_code == 200
        engagement_body = engagement_admin.json()
        assert engagement_body["id"] == str(node_id)
        assert engagement_body["views_count"] >= 1

        comments_admin = client.get(
            f"/v1/admin/nodes/{node_id}/comments",
            headers=admin_headers,
            params={"view": "all", "limit": 20},
        )
        assert comments_admin.status_code == 200
        admin_payload = comments_admin.json()
        assert admin_payload["total"] >= 1
        assert any(item["id"] == str(comment_id) for item in admin_payload["items"])

        status_hide = client.post(
            f"/v1/admin/nodes/comments/{comment_id}/status",
            headers=admin_headers,
            json={"status": "hidden", "reason": "triage"},
        )
        assert status_hide.status_code == 200
        assert status_hide.json()["comment"]["status"] == "hidden"

        status_restore = client.post(
            f"/v1/admin/nodes/comments/{comment_id}/status",
            headers=admin_headers,
            json={"status": "published"},
        )
        assert status_restore.status_code == 200

        lock_resp = client.post(
            f"/v1/admin/nodes/{node_id}/comments/lock",
            headers=admin_headers,
            json={"locked": True, "reason": "maintenance"},
        )
        assert lock_resp.status_code == 200
        assert lock_resp.json()["locked"] is True

        unlock_resp = client.post(
            f"/v1/admin/nodes/{node_id}/comments/lock",
            headers=admin_headers,
            json={"locked": False},
        )
        assert unlock_resp.status_code == 200
        assert unlock_resp.json()["locked"] is False

        disable_resp = client.post(
            f"/v1/admin/nodes/{node_id}/comments/disable",
            headers=admin_headers,
            json={"disabled": True, "reason": "cooldown"},
        )
        assert disable_resp.status_code == 200
        assert disable_resp.json()["disabled"] is True

        enable_resp = client.post(
            f"/v1/admin/nodes/{node_id}/comments/disable",
            headers=admin_headers,
            json={"disabled": False},
        )
        assert enable_resp.status_code == 200
        assert enable_resp.json()["disabled"] is False

        ban_target = "00000000-0000-0000-0000-000000000042"
        ban_resp = client.post(
            f"/v1/admin/nodes/{node_id}/comment-bans",
            headers=admin_headers,
            json={"target_user_id": ban_target, "reason": "spam"},
        )
        assert ban_resp.status_code == 200
        assert ban_resp.json()["target_user_id"] == ban_target

        bans_list = client.get(
            f"/v1/admin/nodes/{node_id}/comment-bans",
            headers=admin_headers,
        )
        assert bans_list.status_code == 200
        assert any(item["target_user_id"] == ban_target for item in bans_list.json())

        delete_ban = client.delete(
            f"/v1/admin/nodes/{node_id}/comment-bans/{ban_target}",
            headers=admin_headers,
        )
        assert delete_ban.status_code == 200
        assert delete_ban.json()["ok"] is True

        analytics_admin = client.get(
            f"/v1/admin/nodes/{node_id}/analytics",
            headers=admin_headers,
            params={"limit": 5},
        )
        assert analytics_admin.status_code == 200
        analytics_body = analytics_admin.json()
        assert analytics_body["views"]["total"] >= 1

        analytics_csv = client.get(
            f"/v1/admin/nodes/{node_id}/analytics",
            headers=admin_headers,
            params={"format": "csv"},
        )
        assert analytics_csv.status_code == 200
        assert analytics_csv.headers["content-type"].startswith("text/csv")
        comments = client.get(f"/v1/nodes/{node_id}/comments")
        assert comments.status_code == 200
        items = comments.json()["items"]
        assert items and items[0]["id"] == comment_id

        delete_resp = client.delete(
            f"/v1/nodes/comments/{comment_id}",
            params={"reason": "cleanup"},
            headers=headers,
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["ok"] is True

        deleted_list = client.get(
            f"/v1/nodes/{node_id}/comments",
            params={"includeDeleted": True},
        )
        assert deleted_list.status_code == 200
        deleted_items = deleted_list.json()["items"]
        assert deleted_items and deleted_items[0]["status"] == "deleted"
