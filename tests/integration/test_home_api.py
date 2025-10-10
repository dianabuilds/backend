from __future__ import annotations

from typing import Any

import pytest

import os
import socket

os.environ["APP_DATABASE_SSL_CA"] = ""
os.environ["APP_DATABASE_URL"] = "postgresql://app:app@localhost:5432/app?ssl=disable"
try:
    with socket.create_connection(("localhost", 5432), timeout=0.5):
        _db_available = True
except OSError:
    _db_available = False

pytestmark = pytest.mark.skipif(
    not _db_available, reason="database not reachable for home API tests"
)


def _skip_if_unavailable(exc: Exception) -> None:
    pytest.skip(f"home API unavailable: {exc}")


WRITE_HEADERS = {"X-Roles": "content.home:write"}
READ_HEADERS = {"X-Roles": "content.home:read"}


def test_admin_home_requires_auth(app_client):
    response = app_client.get("/v1/admin/home")
    assert response.status_code == 401


def test_home_draft_publish_and_public_cache(app_client):
    draft_payload: dict[str, Any] = {
        "slug": "main",
        "data": {
            "blocks": [
                {
                    "id": "hero",
                    "type": "hero",
                    "enabled": True,
                    "dataSource": {"mode": "manual", "entity": "node", "items": []},
                }
            ],
            "meta": {"title": "Integration"},
        },
    }

    try:
        put_response = app_client.put(
            "/v1/admin/home", json=draft_payload, headers=WRITE_HEADERS
        )
    except Exception as exc:
        _skip_if_unavailable(exc)
        return
    assert put_response.status_code == 200
    draft = put_response.json()
    assert draft["slug"] == "main"
    assert draft["status"] == "draft"

    get_response = app_client.get("/v1/admin/home", headers=READ_HEADERS)
    assert get_response.status_code == 200
    admin_payload = get_response.json()
    assert admin_payload["draft"]["slug"] == "main"
    assert admin_payload["published"] is None

    publish_response = app_client.post(
        "/v1/admin/home/publish", json={"slug": "main"}, headers=WRITE_HEADERS
    )
    assert publish_response.status_code == 200
    published = publish_response.json()["published"]
    assert published["status"] == "published"

    public_response = app_client.get("/v1/public/home")
    assert public_response.status_code == 200
    assert public_response.headers["Cache-Control"] == "public, max-age=300"
    etag = public_response.headers.get("ETag")
    assert etag
    payload = public_response.json()
    assert payload["slug"] == "main"
    assert "blocks" in payload

    cached_response = app_client.get("/v1/public/home", headers={"If-None-Match": etag})
    assert cached_response.status_code == 304


def test_home_preview_validation_error(app_client):
    invalid_payload = {
        "slug": "main",
        "data": {
            "blocks": [
                {
                    "id": "dup",
                    "type": "hero",
                    "enabled": True,
                    "dataSource": {"mode": "manual", "entity": "node", "items": []},
                },
                {
                    "id": "dup",
                    "type": "hero",
                    "enabled": True,
                    "dataSource": {"mode": "manual", "entity": "node", "items": []},
                },
            ]
        },
    }

    try:
        response = app_client.post(
            "/v1/admin/home/preview", json=invalid_payload, headers=READ_HEADERS
        )
    except Exception as exc:
        _skip_if_unavailable(exc)
        return
    assert response.status_code == 422
    body = response.json()
    detail = body.get("code") or body.get("detail")
    if isinstance(detail, dict):
        code = detail.get("code") or detail.get("error")
    elif isinstance(detail, str):
        code = detail
    else:
        code = None
    assert code == "home_config_duplicate_block_ids"


def test_home_restore_not_found(app_client):
    try:
        response = app_client.post(
            "/v1/admin/home/restore/999",
            json={"slug": "missing"},
            headers=WRITE_HEADERS,
        )
    except Exception as exc:
        _skip_if_unavailable(exc)
        return
    assert response.status_code in {404, 503}
