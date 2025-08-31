import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE__USERNAME", "test")
os.environ.setdefault("DATABASE__PASSWORD", "test")
os.environ.setdefault("DATABASE__HOST", "localhost")
os.environ.setdefault("DATABASE__NAME", "test")
os.environ.setdefault("JWT__SECRET", "test")
os.environ.setdefault("PAYMENT__JWT_SECRET", "test-pay")
os.environ.setdefault("AUTH__REDIS_URL", "fakeredis://")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.core.db.base import Base
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
        assert jobs[0].name == "job_11"
        assert jobs[-1].name == "job_2"
