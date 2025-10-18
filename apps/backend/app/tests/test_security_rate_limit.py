from __future__ import annotations

import importlib

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient


class FakeLimiter:
    def __init__(self, times: int) -> None:
        self.times = times
        self.calls = 0

    async def __call__(self) -> None:
        self.calls += 1
        if self.calls > self.times:
            raise HTTPException(status_code=429, detail="rate_limited")


_fake_limiters: list[FakeLimiter] = []


def _fake_optional_rate_limiter(*, times: int, seconds: int):
    limiter = FakeLimiter(times)
    _fake_limiters.append(limiter)
    return (Depends(limiter),)


@pytest.fixture()
def patched_rate_limits(monkeypatch):
    _fake_limiters.clear()
    monkeypatch.setattr(
        "packages.fastapi_rate_limit.optional_rate_limiter",
        _fake_optional_rate_limiter,
    )
    module = importlib.import_module("apps.backend.infra.security.rate_limits")
    importlib.reload(module)
    yield module
    importlib.reload(module)


def test_public_rate_limit_enforced(patched_rate_limits):
    module = patched_rate_limits
    nodes_spec = module.PUBLIC_RATE_LIMITS["nodes"]

    app = FastAPI()

    @app.post("/limited", dependencies=nodes_spec.as_dependencies())
    async def limited() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    first_response = client.post("/limited")
    assert first_response.status_code == 200, first_response.json()
    for _ in range(nodes_spec.times - 1):
        assert client.post("/limited").status_code == 200
    response = client.post("/limited")
    assert response.status_code == 429
    assert _fake_limiters
    assert _fake_limiters[0].calls == nodes_spec.times + 1


def test_public_rate_limits_payload_matches_specs(patched_rate_limits):
    module = patched_rate_limits
    payload = module.public_rate_limits_payload()
    for key, spec in module.PUBLIC_RATE_LIMITS.items():
        assert key in payload
        assert payload[key]["times"] == spec.times
        assert payload[key]["seconds"] == spec.seconds
