from __future__ import annotations

import importlib
import sys

import httpx
import pytest

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))
from app.core.errors import DomainError  # noqa: E402
from app.domains.ai.providers import AnthropicProvider, OpenAIProvider  # noqa: E402


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_cls", [OpenAIProvider, AnthropicProvider])
@pytest.mark.parametrize(
    "status, code", [(405, "METHOD_NOT_ALLOWED"), (422, "VALIDATION_ERROR")]
)
async def test_client_errors_raise_domain_error(
    provider_cls, status, code, monkeypatch
):
    provider = provider_cls(api_key="k", base_url="http://test")

    calls = {"count": 0}

    async def fake_post(self, url, headers=None, json=None):  # type: ignore[override]
        calls["count"] += 1
        return httpx.Response(status, json={"message": "boom", "extra": 1})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(DomainError) as exc:
        await provider.complete(model="m", prompt="p")
    assert exc.value.code == code
    assert exc.value.status_code == status
    assert exc.value.details == {"message": "boom", "extra": 1}
    assert calls["count"] == 1
