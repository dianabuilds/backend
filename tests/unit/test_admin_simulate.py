import os
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("TESTING", "True")
# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.main import app
from apps.backend.app.domains.registry import register_domain_routers
from app.domains.navigation.api.admin_transitions_router import admin_required

register_domain_routers(app)


async def _admin_dep():
    return SimpleNamespace(id="admin", role="admin")


app.dependency_overrides[admin_required] = _admin_dep

client = TestClient(app)


def test_simulate_endpoint_returns_trace():
    payload = {"start": "a", "graph": {"a": ["b", "c"], "b": []}, "steps": 2, "seed": 1}
    resp = client.post("/admin/transitions/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "trace" in data
    assert isinstance(data["trace"], list)
