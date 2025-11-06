from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from domains.product.navigation.api.public import transition as transition_api
from domains.product.navigation.application.use_cases.transition import TransitionError


@dataclass
class StubHandler:
    payload: dict
    error: TransitionError | None = None

    def execute(self, command):
        if self.error is not None:
            raise self.error
        return type("Result", (), {"payload": self.payload})()


@pytest.fixture()
def app(monkeypatch):
    router = APIRouter(prefix="/navigation")
    handler = StubHandler(payload={"ok": True})

    class _NoRateLimit:
        def as_dependencies(self):
            return ()

    def fake_build(container):
        return handler

    async def override_container():
        return object()

    async def override_current_user():
        return {"sub": "user-1"}

    async def override_csrf():
        return None

    monkeypatch.setitem(transition_api.PUBLIC_RATE_LIMITS, "navigation", _NoRateLimit())
    transition_api.register_transition_routes(router)
    application = FastAPI()
    application.include_router(router)

    application.dependency_overrides[transition_api.get_container] = override_container
    application.dependency_overrides[transition_api.get_current_user] = (
        override_current_user
    )
    application.dependency_overrides[transition_api.csrf_protect] = override_csrf
    monkeypatch.setattr(transition_api, "build_transition_handler", fake_build)

    return application, handler


def test_transition_next_returns_payload(app):
    application, handler = app
    client = TestClient(application)

    response = client.post(
        "/navigation/next",
        json={"origin_node_id": 1, "route_window": [1, 2]},
        headers={"X-Session-Id": "session123"},
    )

    assert response.status_code == 200
    assert response.json() == handler.payload


def test_transition_next_translates_errors(app):
    application, handler = app
    handler.error = TransitionError("forbidden", status_code=403)
    client = TestClient(application)

    response = client.post("/navigation/next", json={})

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
