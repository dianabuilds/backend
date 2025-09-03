from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

import fakeredis.aioredis
from apps.backend.app.core.config import settings
from apps.backend.app.core.policy import policy
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("TESTING", "True")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.core.rate_limit import RateLimitMiddleware  # noqa: E402


def test_rate_limit_middleware_concurrent_requests():
    app = FastAPI()
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app.add_middleware(
        RateLimitMiddleware,
        capacity=5,
        fill_rate=1,
        burst=0,
        redis_client=redis,
    )

    @app.get("/ping")
    async def ping():  # pragma: no cover - used in test
        return {"ok": True}

    headers = {
        "X-Workspace-ID": "ws",
        "X-User-ID": "user",
        "X-Operation": "ping",
    }

    async def _make_requests():
        transport = ASGITransport(app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            tasks = [client.get("/ping", headers=headers) for _ in range(10)]
            return await asyncio.gather(*tasks)

    policy.rate_limit_mode = "enforce"
    settings.rate_limit.enabled = True
    responses = asyncio.run(_make_requests())
    policy.rate_limit_mode = "monitor"
    settings.rate_limit.enabled = False

    success = [r for r in responses if r.status_code == 200]
    failed = [r for r in responses if r.status_code == 429]

    assert len(success) == 10
    assert len(failed) == 0
