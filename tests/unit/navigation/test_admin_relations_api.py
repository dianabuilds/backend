from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from domains.product.navigation.api.admin import relations as admin_relations
from domains.product.navigation.application.use_cases import relations_admin


@dataclass
class StubService:
    payload: Any
    error: relations_admin.RelationsAdminError | None = None

    async def list_strategies(self):
        return self.payload

    async def update_strategy(self, strategy: str, payload: dict[str, Any]):
        if self.error is not None:
            raise self.error
        return {"strategy": strategy, **payload}

    async def overview(self):
        return {"strategies": self.payload}

    async def top_relations(self, algo: str, *, limit: int = 10):
        return {"strategy": algo, "limit": limit}


@pytest.fixture()
def app(monkeypatch):
    router = APIRouter(prefix="/admin")
    stub_service = StubService(payload=[{"strategy": "tags"}])

    def fake_build(container):
        return stub_service

    async def fake_csrf():
        return None

    def admin_dependency():
        return True

    monkeypatch.setattr(admin_relations, "build_relations_admin_service", fake_build)
    monkeypatch.setattr(admin_relations, "csrf_protect", fake_csrf)

    admin_relations.register_admin_relations_routes(router, admin_dependency)

    application = FastAPI()
    application.include_router(router)

    async def override_container():
        return object()

    application.dependency_overrides[admin_relations.get_container] = override_container

    return application, stub_service


def test_admin_list_strategies_returns_payload(app):
    application, stub_service = app
    client = TestClient(application)

    response = client.get("/admin/relations/strategies")

    assert response.status_code == 200
    assert response.json() == stub_service.payload


def test_admin_update_strategy_translates_errors(app):
    application, stub_service = app
    stub_service.error = relations_admin.RelationsUnavailableError()
    client = TestClient(application)

    response = client.patch(
        "/admin/relations/strategies/tags",
        json={"weight": 1.0},
        headers={"X-CSRF-Token": "token"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "storage_unavailable"


def test_admin_routes_forward_arguments(app):
    application, stub_service = app
    stub_service.error = None
    client = TestClient(application)

    response = client.get("/admin/relations/top", params={"algo": "mix", "limit": 5})

    assert response.status_code == 200
    assert response.json() == {"strategy": "mix", "limit": 5}

    overview = client.get("/admin/relations/overview")
    assert overview.status_code == 200
    assert overview.json()["strategies"] == stub_service.payload
