from __future__ import annotations

from typing import Any, Iterator

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api_gateway.main import create_app
from app.api_gateway import idempotency as idempotency_mod
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin


TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "admin-test-user"


@pytest.fixture()
def profile_client() -> Iterator[TestClient]:
    app = create_app(contour="all")

    _override_security_dependencies(app)

    with TestClient(app) as client:
        yield client


def _override_security_dependencies(app) -> None:
    async def _fake_current_user(request: Request) -> dict[str, Any]:
        path = request.url.path
        if path.startswith("/v1/me/"):
            return {"sub": TEST_USER_ID, "role": "user"}
        return {"sub": ADMIN_USER_ID, "role": "admin"}

    async def _noop_csrf(_: Request) -> None:  # pragma: no cover - simple stub
        return None

    async def _noop_require_admin(_: Request) -> None:
        return None

    app.dependency_overrides[get_current_user] = _fake_current_user
    app.dependency_overrides[csrf_protect] = _noop_csrf
    app.dependency_overrides[require_admin] = _noop_require_admin


class _DummyIdempotencyStore:
    def __init__(self, accept: bool = True) -> None:
        self.accept = accept
        self.keys: list[str] = []

    async def reserve(self, key: str) -> bool:
        self.keys.append(key)
        return self.accept


def test_personal_profile_get_returns_profile(profile_client: TestClient) -> None:
    response = profile_client.get("/v1/me/settings/profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["id"] == TEST_USER_ID
    assert "schema_version" in payload
    assert "ETag" in response.headers
    limits = payload["rate_limits"]
    assert "username" in limits and "email" in limits
    assert {"can_change", "next_change_at"} <= limits["username"].keys()
    assert {"can_change", "next_change_at"} <= limits["email"].keys()


def test_personal_profile_put_requires_if_match(profile_client: TestClient) -> None:
    response = profile_client.put(
        "/v1/me/settings/profile",
        json={"bio": "hello"},
    )
    assert response.status_code == 428
    assert response.json()["error"]["code"] == "E_ETAG_REQUIRED"


def test_personal_profile_put_updates_profile(profile_client: TestClient) -> None:
    initial = profile_client.get("/v1/me/settings/profile")
    assert initial.status_code == 200
    etag = initial.headers["ETag"]

    update = profile_client.put(
        "/v1/me/settings/profile",
        headers={"If-Match": etag},
        json={"bio": "updated bio"},
    )
    assert update.status_code == 200
    body = update.json()
    assert body["profile"]["bio"] == "updated bio"
    assert update.headers["ETag"] != etag
    assert "username" in body["rate_limits"]


def test_email_request_change_requires_header(profile_client: TestClient) -> None:
    response = profile_client.post(
        "/v1/me/settings/profile/email/request-change",
        json={"email": "user2@example.com"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "E_IDEMPOTENCY_KEY_REQUIRED"


def test_email_request_and_confirm_flow(
    profile_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _DummyIdempotencyStore()
    monkeypatch.setattr(
        idempotency_mod, "_get_store", lambda settings: store, raising=True
    )

    request_change = profile_client.post(
        "/v1/me/settings/profile/email/request-change",
        headers={idempotency_mod.IDEMPOTENCY_HEADER: "req-1"},
        json={"email": "new@example.com"},
    )
    assert request_change.status_code == 200
    change_payload = request_change.json()
    assert change_payload["status"] == "pending"
    token = change_payload["token"]
    assert token
    assert store.keys == ["req-1"]

    confirm = profile_client.post(
        "/v1/me/settings/profile/email/confirm",
        json={"token": token},
    )
    assert confirm.status_code == 200
    confirmed = confirm.json()
    assert confirmed["profile"]["email"] == "new@example.com"


def test_wallet_bind_and_unbind(profile_client: TestClient) -> None:
    bind = profile_client.post(
        "/v1/me/settings/profile/wallet",
        json={"address": "0xabc123", "chain_id": "1"},
    )
    assert bind.status_code == 200
    bound = bind.json()
    assert bound["profile"]["wallet"]["address"] == "0xabc123"
    assert bound["profile"]["wallet"]["chain_id"] == "1"
    assert "username" in bound["rate_limits"]

    unbind = profile_client.delete("/v1/me/settings/profile/wallet")
    assert unbind.status_code == 200
    cleared = unbind.json()
    assert cleared["profile"]["wallet"]["address"] is None
    assert cleared["profile"]["wallet"]["chain_id"] is None
    assert "email" in cleared["rate_limits"]


def test_admin_profile_get_not_found(profile_client: TestClient) -> None:
    response = profile_client.get(
        "/v1/settings/profile/00000000-0000-0000-0000-00000000ffff"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "E_PROFILE_NOT_FOUND"


def test_admin_profile_put_success(profile_client: TestClient) -> None:
    initial = profile_client.get(f"/v1/settings/profile/{TEST_USER_ID}")
    assert initial.status_code == 200
    etag = initial.headers["ETag"]

    update = profile_client.put(
        f"/v1/settings/profile/{TEST_USER_ID}",
        headers={"If-Match": etag},
        json={"avatar_url": "https://cdn.example.com/avatar.png"},
    )
    assert update.status_code == 200
    data = update.json()
    assert data["profile"]["avatar_url"] == "https://cdn.example.com/avatar.png"
    assert update.headers["ETag"] != etag
    assert "username" in data["rate_limits"]


def test_admin_profile_put_invalid_payload(profile_client: TestClient) -> None:
    current = profile_client.get(f"/v1/settings/profile/{TEST_USER_ID}")
    assert current.status_code == 200
    etag = current.headers["ETag"]

    response = profile_client.put(
        f"/v1/settings/profile/{TEST_USER_ID}",
        headers={"If-Match": etag},
        json={"username": ""},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "E_USERNAME_REQUIRED"


def test_wallet_bind_requires_signature_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_PROFILE_REQUIRE_WALLET_SIGNATURE", "true")
    app = create_app(contour="all")
    _override_security_dependencies(app)
    with TestClient(app) as client:
        missing = client.post(
            "/v1/me/settings/profile/wallet",
            json={"address": "0xabc"},
        )
        assert missing.status_code == 400
        assert missing.json()["error"]["code"] == "E_WALLET_SIGNATURE_REQUIRED"

        ok = client.post(
            "/v1/me/settings/profile/wallet",
            json={"address": "0xabc", "chain_id": "1", "signature": "f" * 32},
        )
        assert ok.status_code == 200
