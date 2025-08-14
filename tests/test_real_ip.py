import pytest
from starlette.requests import Request

from app.core.real_ip import get_real_ip
from app.core.config import settings


def _req(client_ip: str, headers: dict[str, str]):
    scope = {
        "type": "http",
        "client": (client_ip, 1234),
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_real_ip_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings.real_ip, "enabled", True)
    monkeypatch.setattr(settings.real_ip, "trusted_proxies", ["1.1.1.1"])
    req = _req("1.1.1.1", {"X-Forwarded-For": "5.5.5.5, 1.1.1.1"})
    assert get_real_ip(req) == "5.5.5.5"


@pytest.mark.asyncio
async def test_real_ip_untrusted(monkeypatch):
    monkeypatch.setattr(settings.real_ip, "enabled", True)
    monkeypatch.setattr(settings.real_ip, "trusted_proxies", ["1.1.1.1"])
    req = _req("9.9.9.9", {"X-Forwarded-For": "5.5.5.5"})
    assert get_real_ip(req) == "9.9.9.9"
