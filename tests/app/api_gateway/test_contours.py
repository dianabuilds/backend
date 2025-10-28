from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api_gateway.main import create_app
from tests.conftest import make_jwt


def _collect_paths(app) -> set[str]:
    schema = app.openapi()
    return set(schema.get("paths", {}))


def test_public_contour_exposes_only_public_routes() -> None:
    app = create_app(contour="public")
    paths = _collect_paths(app)
    assert "/v1/nodes" in paths
    assert "/v1/profile/me" in paths
    assert not any(path.startswith("/v1/admin") for path in paths)
    assert all("/api/moderation" not in path for path in paths)


def test_admin_contour_exposes_only_admin_routes() -> None:
    app = create_app(contour="admin")
    paths = _collect_paths(app)
    assert "/v1/profile" not in paths
    assert "/v1/admin/profile/{user_id}" in paths
    assert "/v1/admin/profile/{user_id}/username" in paths
    assert all(
        path.startswith("/v1/admin")
        or path.startswith("/api/moderation")
        or path.startswith("/v1/notifications/admin")
        for path in paths
        if path.startswith("/v1") or path.startswith("/api")
    )


def test_ops_contour_exposes_operations_routes() -> None:
    app = create_app(contour="ops")
    paths = _collect_paths(app)
    assert any(path.startswith("/v1/billing") for path in paths)


def test_audience_middleware_enforces_admin_tokens() -> None:
    app = create_app(contour="admin")

    @app.get("/__ping")
    def _ping() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/__ping")
    assert response.status_code == 401

    admin_token = make_jwt("admin-user", role="admin", audience="admin")
    client.cookies.set("access_token", admin_token)
    response = client.get("/__ping")
    assert response.status_code == 200

    client.cookies.set(
        "access_token", make_jwt("user-id", role="user", audience="public")
    )
    response = client.get("/__ping")
    assert response.status_code == 403


def test_ops_middleware_requires_finance_role() -> None:
    app = create_app(contour="ops")

    @app.get("/__ops-ping")
    def _ops_ping() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/__ops-ping").status_code == 401

    ops_token = make_jwt("ops-user", role="finance_ops", audience="ops")
    client.cookies.set("access_token", ops_token)
    assert client.get("/__ops-ping").status_code == 200

    client.cookies.set(
        "access_token", make_jwt("bad-user", role="user", audience="public")
    )
    assert client.get("/__ops-ping").status_code == 403


def test_admin_api_key_allows_access_without_token() -> None:
    os.environ["APP_ADMIN_API_KEY"] = "admin-key-test"
    try:
        app = create_app(contour="admin")

        @app.get("/__check")
        def _check() -> dict[str, bool]:
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/__check", headers={"X-Admin-Key": "admin-key-test"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}

        bad = client.get("/__check", headers={"X-Admin-Key": "wrong"})
        assert bad.status_code == 401
    finally:
        os.environ.pop("APP_ADMIN_API_KEY", None)
        os.environ.pop("ADMIN_API_KEY", None)


def test_ops_api_key_allows_access_without_token() -> None:
    os.environ["APP_OPS_API_KEY"] = "ops-key-test"
    try:
        app = create_app(contour="ops")

        @app.get("/__ops-check")
        def _ops_check() -> dict[str, bool]:
            return {"ok": True}

        client = TestClient(app)
        ok = client.get("/__ops-check", headers={"X-Ops-Key": "ops-key-test"})
        assert ok.status_code == 200
        assert ok.json() == {"ok": True}

        bad = client.get("/__ops-check", headers={"X-Ops-Key": "wrong"})
        assert bad.status_code == 401
    finally:
        os.environ.pop("APP_OPS_API_KEY", None)
        os.environ.pop("OPS_API_KEY", None)
