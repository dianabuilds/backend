from __future__ import annotations

import os
import sys
from pathlib import Path

import fakeredis.aioredis
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE__USERNAME", "test")
os.environ.setdefault("DATABASE__PASSWORD", "test")
os.environ.setdefault("DATABASE__HOST", "localhost")
os.environ.setdefault("DATABASE__NAME", "test")
os.environ.setdefault("JWT__SECRET", "test")
os.environ.setdefault("PAYMENT__JWT_SECRET", "test-pay")
os.environ.setdefault("REDIS_URL", "fakeredis://")
os.environ.setdefault("TESTING", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.admin.application.jobs_service import JobsService
from app.models.background_job_history import BackgroundJobHistory


@pytest.mark.asyncio
async def test_get_recent_jobs():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BackgroundJobHistory.__table__.create)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        for i in range(12):
            await JobsService.record_run(session, f"job_{i}", "success")
        jobs = await JobsService.get_recent(session)
        assert len(jobs) == 10
        assert jobs[0]["name"] == "job_11"
        assert jobs[-1]["name"] == "job_2"


@pytest.mark.asyncio
async def test_get_queue_stats(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis()
    await fake.flushall()
    # setup BullMQ-like keys
    await fake.set("alpha:meta", "1")
    await fake.rpush("alpha:wait", "a1", "a2")
    await fake.rpush("alpha:active", "a3")
    await fake.set("beta:meta", "1")
    await fake.rpush("beta:wait", "b1")

    def fake_redis(url: str, **_: object):
        return fake

    monkeypatch.setattr(
        "app.domains.admin.application.jobs_service.create_async_redis", fake_redis
    )
    monkeypatch.setattr(
        "app.domains.admin.application.jobs_service.settings",  # type: ignore[attr-defined]
        type("S", (), {"queue_broker_url": "redis://", "async_enabled": True}),
    )

    stats = await JobsService.get_queue_stats()
    assert stats == {
        "alpha": {"pending": 2, "active": 1},
        "beta": {"pending": 1, "active": 0},
    }
