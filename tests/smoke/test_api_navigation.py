from __future__ import annotations

from uuid import uuid4

from packages.core.config import load_settings
from tests.conftest import add_auth, make_jwt


class _StubNodesPort:
    def __init__(self, nodes: list[dict]):
        self._nodes = list(nodes)

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
        return [n for n in self._nodes if n["author_id"] == author_id][offset : offset + limit]

    def get(self, node_id: int):
        for node in self._nodes:
            if int(node["id"]) == int(node_id):
                return node
        return None


def _csrf_headers() -> dict[str, str]:
    settings = load_settings()
    return {settings.auth_csrf_header_name: "csrf-test"}


def test_navigation_next_no_candidates(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid)
    add_auth(app_client, tok)

    container = app_client.app.state.container
    original_nodes = container.navigation_service.nodes
    container.navigation_service.nodes = _StubNodesPort([])
    try:
        response = app_client.post(
            "/v1/navigation/next",
            json={"session_id": "sess-empty", "mode": "normal"},
            headers=_csrf_headers(),
        )
    finally:
        container.navigation_service.nodes = original_nodes
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ui_slots"] == 0
    assert body["decision"]["empty_pool"] is True
    assert body["decision"]["candidates"] == []
    assert "fallback_suggestions" in body


def test_navigation_next_with_candidates(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid)
    add_auth(app_client, tok)

    container = app_client.app.state.container
    original_nodes = container.navigation_service.nodes
    nodes = [
        {"id": 1, "author_id": uid, "title": "First", "tags": ["caves"], "is_public": True},
        {
            "id": 2,
            "author_id": uid,
            "title": "Second",
            "tags": ["caves", "explore"],
            "is_public": True,
        },
    ]
    container.navigation_service.nodes = _StubNodesPort(nodes)
    try:
        response = app_client.post(
            "/v1/navigation/next",
            json={
                "session_id": "sess-candidates",
                "origin_node_id": 1,
                "route_window": [1],
                "mode": "normal",
            },
            headers=_csrf_headers(),
        )
    finally:
        container.navigation_service.nodes = original_nodes
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"]["empty_pool"] is False
    assert body["ui_slots"] >= 1
    candidates = body["decision"]["candidates"]
    assert candidates, "expected at least one candidate"
    sample = candidates[0]
    assert {"id", "badge", "score", "probability", "reason", "explain", "provider"} <= set(
        sample.keys()
    )
    assert sample["reason"]
    assert body["cache_seed"]
    assert body["limit_state"] == "normal"
