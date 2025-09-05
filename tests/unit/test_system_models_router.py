import importlib
import sys

# ruff: noqa: E402
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

import app.domains.ai.api.system_models_router as module  # noqa: E402


class DummyRepo:  # pragma: no cover - stub
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def list_models(self):  # pragma: no cover - unused
        return []

    async def upsert_model(self, **kwargs):
        class Row:
            def __init__(self, code: str) -> None:
                self.code = code

            def as_dict(self):
                return {"code": self.code}

        return Row(kwargs.get("code"))


async def _fake_db():
    yield None


@pytest.fixture(autouse=True)
def _patch_dependencies(monkeypatch):
    monkeypatch.setattr(module, "AISystemModelRepository", DummyRepo)
    from typing import Annotated

    from fastapi import Depends

    module.AdminRequired = Annotated[None, Depends(lambda: None)]


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(module.router)
    app.dependency_overrides[module.get_db] = _fake_db
    return TestClient(app)


def test_add_model(client: TestClient) -> None:
    resp = client.post("/admin/ai/system/models", json={"code": "gpt-4"})
    assert resp.status_code == 200
    assert resp.json()["code"] == "gpt-4"
