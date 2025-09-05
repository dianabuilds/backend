import importlib
import sys

# ruff: noqa: E402
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

import app.domains.ai.api.system_providers_router as providers_module  # noqa: E402


class DummyService:
    def __init__(self, repo):  # pragma: no cover - unused
        pass

    async def update_ai_settings(self, **kwargs):
        return {"provider": kwargs.get("provider"), "base_url": kwargs.get("base_url")}

    async def get_ai_settings(self):  # pragma: no cover
        return {"provider": "openai", "base_url": "https://api.example"}


class DummyRepo:  # pragma: no cover - stub
    def __init__(self, *args, **kwargs) -> None:
        pass


async def _fake_db():
    yield None


@pytest.fixture(autouse=True)
def _patch_dependencies(monkeypatch):
    monkeypatch.setattr("app.domains.ai.api.system_providers_router.SettingsService", DummyService)
    monkeypatch.setattr(
        "app.domains.ai.api.system_providers_router.AISettingsRepository", DummyRepo
    )
    from typing import Annotated

    from fastapi import Depends

    providers_module.AdminRequired = Annotated[None, Depends(lambda: None)]


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(providers_module.router)
    app.dependency_overrides[providers_module.get_db] = _fake_db
    return TestClient(app)


def test_add_provider(client: TestClient) -> None:
    resp = client.post("/admin/ai/system/providers", json={"code": "openai"})
    assert resp.status_code == 200
    assert resp.json()["code"] == "openai"
