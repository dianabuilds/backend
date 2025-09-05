import importlib.util
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
    spec = importlib.util.spec_from_file_location("app.core.settings", core_path / "settings.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["app.core.settings"] = module
    spec.loader.exec_module(module)
    return module.Settings


def _load_env_loader():
    core_path = Path(__file__).resolve().parents[2] / "apps/backend/app/core"
    spec = importlib.util.spec_from_file_location(
        "app.core.env_loader", core_path / "env_loader.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["app.core.env_loader"] = module
    spec.loader.exec_module(module)
    return module.load_dotenv


def _set_db_env(monkeypatch):
    monkeypatch.setenv("DATABASE__USERNAME", "x")
    monkeypatch.setenv("DATABASE__PASSWORD", "x")
    monkeypatch.setenv("DATABASE__HOST", "x")
    monkeypatch.setenv("DATABASE__NAME", "x")
    monkeypatch.setenv("DATABASE__PORT", "1")
    monkeypatch.setenv("DATABASE__DRIVER", "postgresql")


def test_blank_cors_in_dotenv(tmp_path, monkeypatch):
    Settings = _load_settings_cls()
    load_dotenv = _load_env_loader()
    env_file = tmp_path / ".env"
    env_file.write_text("APP_CORS_ALLOW_ORIGINS=\n")
    _set_db_env(monkeypatch)
    load_dotenv(env_file, override=True)
    settings = Settings()
    assert settings.cors_allow_origins == []
