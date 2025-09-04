from __future__ import annotations

import importlib
import logging
import os
import sys

import pytest

os.environ.setdefault("TESTING", "True")
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.api import health as health_module  # noqa: E402
from app.core.config import settings  # noqa: E402


class DummyResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [405, 422, 500])
async def test_check_payment_service_non_2xx(
    monkeypatch, caplog, status_code: int
) -> None:
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(settings.payment, "api_base", "http://example.test")

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
            pass

        async def __aenter__(self) -> DummyClient:  # pragma: no cover - simple stub
            return self

        async def __aexit__(
            self, exc_type, exc, tb
        ) -> None:  # pragma: no cover - simple stub
            return None

        async def get(
            self, url: str
        ) -> DummyResponse:  # pragma: no cover - simple stub
            return DummyResponse(status_code)

    monkeypatch.setattr(health_module.httpx, "AsyncClient", DummyClient)

    ok = await health_module._check_payment_service(timeout=0.1)
    assert ok is False
    assert str(status_code) in caplog.text
