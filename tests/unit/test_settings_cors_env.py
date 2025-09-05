import importlib.util
import json
import sys
import types
from pathlib import Path


def _load_settings_cls():
    core_path = Path(__file__).resolve().parents[2] / "apps/backend/app/core"
    app_module = types.ModuleType("app")
    core_module = types.ModuleType("app.core")
    core_module.__path__ = [str(core_path)]
    app_module.core = core_module
    sys.modules.setdefault("app", app_module)
    sys.modules.setdefault("app.core", core_module)
    spec = importlib.util.spec_from_file_location(
        "app.core.settings", core_path / "settings.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["app.core.settings"] = module
    spec.loader.exec_module(module)
    return module.Settings


def _set_db_env(monkeypatch):
    monkeypatch.setenv("DATABASE__USERNAME", "x")
    monkeypatch.setenv("DATABASE__PASSWORD", "x")
    monkeypatch.setenv("DATABASE__HOST", "x")
    monkeypatch.setenv("DATABASE__NAME", "x")
    monkeypatch.setenv("DATABASE__PORT", "1")
    monkeypatch.setenv("DATABASE__DRIVER", "postgresql")


def test_empty_cors_origins(monkeypatch):
    Settings = _load_settings_cls()
    _set_db_env(monkeypatch)
    monkeypatch.setenv("APP_CORS_ALLOW_ORIGINS", json.dumps([]))
    settings = Settings()
    assert settings.cors_allow_origins == []


def test_json_cors_origins(monkeypatch):
    Settings = _load_settings_cls()
    _set_db_env(monkeypatch)
    monkeypatch.setenv(
        "APP_CORS_ALLOW_ORIGINS",
        json.dumps(["https://a.example", "https://b.example"]),
    )
    settings = Settings()
    assert settings.cors_allow_origins == [
        "https://a.example",
        "https://b.example",
    ]


def test_lowercase_cors_origins(monkeypatch):
    Settings = _load_settings_cls()
    _set_db_env(monkeypatch)
    monkeypatch.setenv("cors_allow_origins", "https://a.example, https://b.example")
    from app.core.env_loader import _normalize_env_for_pydantic_json

    _normalize_env_for_pydantic_json()
    settings = Settings()
    assert settings.cors_allow_origins == [
        "https://a.example",
        "https://b.example",
    ]
