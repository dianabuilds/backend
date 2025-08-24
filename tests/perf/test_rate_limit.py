import asyncio
import importlib
import os
import sys
from pathlib import Path

import fakeredis.aioredis
import httpx
from fastapi import FastAPI

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
        burst=2,
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
        async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
            results = []
            for _ in range(10):
                results.append(await client.get("/ping", headers=headers))
            return results

    responses = asyncio.run(_make_requests())

    success = [r for r in responses if r.status_code == 200]
    failed = [r for r in responses if r.status_code == 429]

    assert len(success) == 7
    assert len(failed) == 3
    assert "Retry-After" in failed[0].headers
