from __future__ import annotations

import importlib
import logging
import os
import sys

import httpx
import pytest

os.environ.setdefault("TESTING", "True")
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.api import health as health_module  # noqa: E402


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [500, 405, 422])
async def test_check_ai_service_logs_status(
    monkeypatch, caplog, status_code: int
) -> None:
    caplog.set_level(logging.ERROR)

    def failing_embedding(_: str) -> list[int]:  # pragma: no cover - helper
        request = httpx.Request("POST", "http://example.test")
        response = httpx.Response(status_code, request=request)
        raise httpx.HTTPStatusError("boom", request=request, response=response)

    monkeypatch.setattr(health_module, "get_embedding", failing_embedding)

    ok = await health_module._check_ai_service(timeout=0.1)

    assert ok is False
    assert str(status_code) in caplog.text
