from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domains.platform.moderation.api.http import (
    router as moderation_router,
)
from domains.platform.moderation.application.service import (
    PlatformModerationService,
)

ADMIN_HEADERS = {"X-Roles": "Admin"}


@pytest.fixture(scope="session")
def moderation_client() -> TestClient:
    service = PlatformModerationService(seed_demo=True)
    settings = SimpleNamespace(
        env="test",
        database_url=None,
        admin_api_key="integration-admin",
        auth_jwt_secret="secret",
        auth_jwt_algorithm="HS256",
        auth_csrf_cookie_name="csrftest",
    )
    container = SimpleNamespace(
        settings=settings,
        platform_moderation=SimpleNamespace(service=service),
    )
    app = FastAPI()
    app.state.container = container
    app.include_router(moderation_router)
    with TestClient(app) as client:
        yield client


def test_moderation_content_flow(moderation_client: TestClient) -> None:
    queue_response = moderation_client.get(
        "/api/moderation/content", headers=ADMIN_HEADERS
    )
    assert queue_response.status_code == 200
    data = queue_response.json()
    assert "items" in data

    items = data["items"]
    if not items:
        return

    content_id = items[0]["id"]

    detail_response = moderation_client.get(
        f"/api/moderation/content/{content_id}", headers=ADMIN_HEADERS
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == content_id

    decision_response = moderation_client.post(
        f"/api/moderation/content/{content_id}/decision",
        headers=ADMIN_HEADERS,
        json={"action": "keep", "reason": "integration-check", "actor": "integration"},
    )
    assert decision_response.status_code == 200
    decision_payload = decision_response.json()
    assert decision_payload["status"]


def test_moderation_appeals_overview(moderation_client: TestClient) -> None:
    list_response = moderation_client.get(
        "/api/moderation/appeals", headers=ADMIN_HEADERS
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert "items" in data

    items = data["items"]
    if not items:
        return

    appeal_id = items[0]["id"]
    detail_response = moderation_client.get(
        f"/api/moderation/appeals/{appeal_id}", headers=ADMIN_HEADERS
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == appeal_id


def test_moderation_users_endpoints(moderation_client: TestClient) -> None:
    list_response = moderation_client.get(
        "/api/moderation/users", headers=ADMIN_HEADERS
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert "items" in data

    items = data["items"]
    if not items:
        return

    user_id = items[0]["id"]
    detail_response = moderation_client.get(
        f"/api/moderation/users/{user_id}", headers=ADMIN_HEADERS
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == user_id

    note_response = moderation_client.post(
        f"/api/moderation/users/{user_id}/notes",
        headers=ADMIN_HEADERS,
        json={"text": "integration note", "author_id": "tester"},
    )
    assert note_response.status_code == 200
    note_payload = note_response.json()
    assert note_payload["text"] == "integration note"

    sanction_response = moderation_client.post(
        f"/api/moderation/users/{user_id}/sanctions",
        headers=ADMIN_HEADERS,
        json={"type": "warning", "reason": "integration"},
    )
    assert sanction_response.status_code == 200
    sanction_payload = sanction_response.json()
    sanction_id = sanction_payload.get("id")
    if sanction_id:
        patch_response = moderation_client.patch(
            f"/api/moderation/users/{user_id}/sanctions/{sanction_id}",
            headers=ADMIN_HEADERS,
            json={"status": "canceled"},
        )
        assert patch_response.status_code == 200
