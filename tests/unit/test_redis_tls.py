import importlib
import sys
from pathlib import Path
import ssl

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.core.redis_utils import create_async_redis


def test_rediss_no_ssl_kwarg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_SSL_VERIFY", raising=False)
    captured: dict[str, object] = {}

    class DummyPool:  # pragma: no cover - only used for type compatibility
        pass

    def fake_from_url(url: str, **kwargs) -> DummyPool:  # type: ignore[override]
        nonlocal captured
        captured = kwargs
        return DummyPool()

    monkeypatch.setattr(
        "app.core.redis_utils.redis.BlockingConnectionPool.from_url",
        fake_from_url,
    )
    monkeypatch.setattr(
        "app.core.redis_utils.redis.Redis",
        lambda connection_pool, **kwargs: object(),
    )

    create_async_redis("rediss://localhost:6379/0")

    assert "ssl" not in captured
    assert captured["ssl_cert_reqs"] == ssl.CERT_NONE
    assert captured["ssl_check_hostname"] is False
