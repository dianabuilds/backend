import importlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))
from app.domains.workspaces.api import router as workspaces_router  # noqa: E402

app = FastAPI()
app.include_router(workspaces_router)
client = TestClient(app)


def test_patch_on_collection_not_allowed() -> None:
    resp = client.patch("/workspaces")
    assert resp.status_code == 405


def test_delete_on_collection_not_allowed() -> None:
    resp = client.delete("/workspaces")
    assert resp.status_code == 405


def test_post_on_item_not_allowed() -> None:
    resp = client.post("/workspaces/1")
    assert resp.status_code == 405
