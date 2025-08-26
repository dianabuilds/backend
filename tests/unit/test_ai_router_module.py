import importlib
import sys
from pathlib import Path

# Make "app" package importable like in other tests
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.ai.router import resolve  # noqa: E402


def test_explicit_fallback_to_user(caplog):
    bundle = {
        "mode": "sequential",
        "models": [
            {"name": "m0", "health": False},
            {"name": "m1", "health": True},
        ],
    }
    context = {"explicit": "m0", "user": "m1"}
    with caplog.at_level("INFO"):
        model = resolve(bundle, context)
    assert model["name"] == "m1"
    record = next(r for r in caplog.records if "Resolved model" in r.message)
    assert "source=user" in record.message
    assert "m0->m1" in record.message


def test_weighted_ignores_unhealthy():
    bundle = {
        "mode": "weighted",
        "models": [
            {"name": "m0", "health": False, "weight": 100},
            {"name": "m1", "health": True, "weight": 1},
        ],
    }
    context = {}
    model = resolve(bundle, context)
    assert model["name"] == "m1"


def test_cheapest_selects_low_cost():
    bundle = {
        "mode": "cheapest",
        "models": [
            {"name": "m0", "health": True, "cost": 0.5},
            {"name": "m1", "health": True, "cost": 0.1},
        ],
    }
    context = {}
    model = resolve(bundle, context)
    assert model["name"] == "m1"
