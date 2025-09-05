from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_settings_cls():
    core_path = Path(__file__).resolve().parents[2] / "apps/backend/app/core"
    app_module = types.ModuleType("app")
    core_module = types.ModuleType("app.core")
    core_module.__path__ = [str(core_path)]
    app_module.core = core_module
    sys.modules.setdefault("app", app_module)
    sys.modules.setdefault("app.core", core_module)
    spec = importlib.util.spec_from_file_location("app.core.settings", core_path / "settings.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["app.core.settings"] = module
    spec.loader.exec_module(module)
    return module.Settings


def test_env_file_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in [
        "DATABASE__USERNAME",
        "DATABASE__PASSWORD",
        "DATABASE__HOST",
        "DATABASE__NAME",
        "DATABASE__PORT",
        "JWT__SECRET",
    ]:
        monkeypatch.delenv(var, raising=False)
    env_file = Path(__file__).resolve().parents[2] / ".env"
    env_file.write_text(
        "JWT__SECRET=supersecret\n"
        "DATABASE__USERNAME=test\n"
        "DATABASE__PASSWORD=secret\n"
        "DATABASE__HOST=db.example\n"
        "DATABASE__PORT=1234\n"
        "DATABASE__NAME=mydb\n"
    )
    try:
        Settings = _load_settings_cls()
        settings = Settings()
    finally:
        env_file.unlink()
    assert settings.database.username == "test"
    assert settings.database.password == "secret"
    assert settings.database.host == "db.example"
    assert settings.database.port == 1234
    assert settings.database.name == "mydb"
