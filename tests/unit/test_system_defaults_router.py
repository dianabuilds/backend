import importlib
import sys

# ruff: noqa: E402
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

import app.domains.ai.api.system_defaults_router as module  # noqa: E402


class DummyRepo:  # pragma: no cover - stub
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def get_default(self):  # pragma: no cover - unused
        class Row:
            def as_dict(self):
                return {"provider": "openai", "model": "gpt-4"}

        return Row()

    async def set_default(self, **kwargs):
        class Row:
            def as_dict(self):
                return {
                    "provider": kwargs.get("provider"),
                    "model": kwargs.get("model"),
                }

        return Row()


async def _fake_db():
    yield None


@pytest.fixture(autouse=True)
def _patch_dependencies(monkeypatch):
    monkeypatch.setattr(module, "AIDefaultModelRepository", DummyRepo)
    from typing import Annotated

    from fastapi import Depends

    module.AdminRequired = Annotated[None, Depends(lambda: None)]


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(module.router)
    app.dependency_overrides[module.get_db] = _fake_db
    return TestClient(app)


def test_set_defaults(client: TestClient) -> None:
    resp = client.post("/admin/ai/system/defaults", json={"provider": "openai", "model": "gpt-4"})
    assert resp.status_code == 200
    assert resp.json()["provider"] == "openai"
    assert resp.json()["model"] == "gpt-4"
