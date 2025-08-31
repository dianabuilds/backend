import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.core.settings import Settings  # noqa: E402


def test_redis_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://example.com:6379/0")

    settings = Settings()

    assert settings.cache.redis_url == "redis://example.com:6379/0"
    assert settings.redis_url == "redis://example.com:6379/0"
