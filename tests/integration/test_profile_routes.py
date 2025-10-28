from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.backend.app.api_gateway.main import create_app
from domains.product.profile.adapters.memory.repository import MemoryRepo
from domains.product.profile.application.services import Service
from packages.core import Flags
from tests.conftest import make_jwt

PUBLIC_USER_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000099"


class AllowAllIam:
    def allow(self, subject: dict, action: str, resource: dict) -> bool:
        return True


class DummyOutbox:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict, str | None]] = []

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        self.events.append((topic, payload, key))


class DummyStorageGateway:
    def __init__(self) -> None:
        self.saved: list[tuple[bytes, str, str]] = []

    def save(self, fileobj, filename: str, content_type: str) -> str:
        data = fileobj.read()
        self.saved.append((data, filename, content_type))
        return f"https://cdn.test/{filename}"


def _authenticate(
    client: TestClient, settings, user_id: str, *, role: str
) -> dict[str, str]:
    token = make_jwt(user_id, role=role)
    csrf_value = "csrf-token"
    client.cookies.set("access_token", token)
    client.cookies.set(settings.auth_csrf_cookie_name, csrf_value)
    return {settings.auth_csrf_header_name: csrf_value}


def _build_service() -> Service:
    repo = MemoryRepo()
    return Service(repo=repo, outbox=DummyOutbox(), iam=AllowAllIam(), flags=Flags())


@pytest.fixture()
def public_app() -> Iterator[SimpleNamespace]:
    service = _build_service()
    storage = DummyStorageGateway()
    captured: dict[str, object] = {}

    def container_factory(*, settings, contour, **_: object):
        captured["settings"] = settings
        return SimpleNamespace(
            settings=settings,
            profile_service=service,
            media=SimpleNamespace(storage=storage),
        )

    app = create_app(contour="public", container_factory=container_factory)
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            service=service,
            storage=storage,
            outbox=service.outbox,  # type: ignore[attr-defined]
            settings=captured["settings"],
        )


@pytest.fixture()
def admin_app() -> Iterator[SimpleNamespace]:
    service = _build_service()
    storage = DummyStorageGateway()
    captured: dict[str, object] = {}

    def container_factory(*, settings, contour, **_: object):
        captured["settings"] = settings
        return SimpleNamespace(
            settings=settings,
            profile_service=service,
            media=SimpleNamespace(storage=storage),
        )

    app = create_app(contour="admin", container_factory=container_factory)
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            service=service,
            storage=storage,
            outbox=service.outbox,  # type: ignore[attr-defined]
            settings=captured["settings"],
        )


def test_public_profile_mutations_cover_commands(public_app: SimpleNamespace) -> None:
    headers = _authenticate(
        public_app.client, public_app.settings, PUBLIC_USER_ID, role="user"
    )

    response = public_app.client.get("/v1/profile/me")
    assert response.status_code == 200
    etag = response.headers["etag"]
    assert response.json()["id"] == PUBLIC_USER_ID

    update_headers = dict(headers)
    update_headers["If-Match"] = etag
    response = public_app.client.put(
        "/v1/profile/me",
        json={"bio": "Updated bio"},
        headers=update_headers,
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Updated bio"
    assert public_app.outbox.events[-1][0] == "profile.updated.v1"

    email_headers = dict(headers)
    email_headers["Idempotency-Key"] = "req-1"
    response = public_app.client.post(
        "/v1/profile/me/email/request-change",
        json={"email": "new@example.com"},
        headers=email_headers,
    )
    assert response.status_code == 200
    token = response.json()["token"]
    assert public_app.outbox.events[-1][0] == "profile.email.change.requested.v1"

    response = public_app.client.post(
        "/v1/profile/me/email/confirm",
        json={"token": token},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    assert public_app.outbox.events[-1][0] == "profile.email.updated.v1"

    response = public_app.client.post(
        "/v1/profile/me/wallet",
        json={"address": "0xabc", "chain_id": "1"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["wallet"]["address"] == "0xabc"
    assert public_app.outbox.events[-1][0] == "profile.wallet.updated.v1"

    response = public_app.client.delete("/v1/profile/me/wallet", headers=headers)
    assert response.status_code == 200
    assert response.json()["wallet"]["address"] is None
    assert public_app.outbox.events[-1][0] == "profile.wallet.cleared.v1"


def test_public_avatar_upload_uses_storage_gateway(public_app: SimpleNamespace) -> None:
    headers = _authenticate(
        public_app.client, public_app.settings, PUBLIC_USER_ID, role="user"
    )

    files = {"file": ("avatar.png", b"avatar-bytes", "image/png")}
    response = public_app.client.post(
        "/v1/profile/me/avatar",
        files=files,
        headers=headers,
    )
    assert response.status_code == 200
    assert public_app.storage.saved[0][1] == "avatar.png"


def test_admin_routes_require_admin_auth(admin_app: SimpleNamespace) -> None:
    target = PUBLIC_USER_ID
    response = admin_app.client.get(f"/v1/admin/profile/{target}")
    assert response.status_code == 401


def test_admin_profile_endpoints_allow_full_management(
    admin_app: SimpleNamespace,
) -> None:
    headers = _authenticate(
        admin_app.client, admin_app.settings, ADMIN_USER_ID, role="admin"
    )
    target = PUBLIC_USER_ID

    response = admin_app.client.get(f"/v1/admin/profile/{target}")
    assert response.status_code == 200
    etag = response.headers["etag"]

    update_headers = dict(headers)
    update_headers["If-Match"] = etag
    response = admin_app.client.put(
        f"/v1/admin/profile/{target}",
        json={"bio": "admin-set"},
        headers=update_headers,
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "admin-set"
    assert admin_app.outbox.events[-1][0] == "profile.updated.v1"

    response = admin_app.client.put(
        f"/v1/admin/profile/{target}/username",
        json={"username": "admin-updated"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin-updated"
    assert admin_app.outbox.events[-1][0] == "profile.updated.v1"
