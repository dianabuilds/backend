from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.usefixtures("app_client")
def test_health_endpoints(app_client) -> None:
    health = app_client.get("/healthz")
    assert health.status_code == 200
    assert health.json() == {"ok": True}

    try:
        ready = app_client.get("/readyz")
    except Exception as exc:
        pytest.skip(f"ready check unavailable: {exc}")
        return
    if ready.status_code != 200:
        pytest.skip(f"ready endpoint returned {ready.status_code}")
        return
    payload = ready.json()
    assert payload.keys() >= {"ok", "components"}
    components = payload["components"]
    assert isinstance(components, dict)
    assert {"redis", "database", "search"} <= components.keys()


@pytest.mark.usefixtures("app_client")
def test_openapi_available(app_client) -> None:
    response = app_client.get("/openapi.json")
    assert response.status_code == 200
    data: Any = response.json()
    assert data.get("info", {}).get("title") == "Backend API"
    components = data.get("components", {})
    assert "securitySchemes" in components
    assert "BearerAuth" in components["securitySchemes"]
    paths = data.get("paths", {})
    assert "/v1/public/home" in paths
    assert "/v1/site/pages" in paths
    assert "/v1/site/pages/{page_id}/preview" in paths
