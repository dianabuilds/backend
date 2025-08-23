from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domains.ai.services.generation import process_next_generation_job
from app.domains.ai.recovery import recover_stuck_generation_jobs

logger = logging.getLogger(__name__)


def _make_sessionmaker() -> async_sessionmaker[AsyncSession]:
    # DATABASE_URL должен быть в формате async driver, например: postgresql+asyncpg://...
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    engine = create_async_engine(db_url, pool_pre_ping=True, future=True)
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)


@asynccontextmanager
async def session_scope(sm: async_sessionmaker[AsyncSession]):
    async with sm() as session:
        try:
            yield session
        finally:
            await session.close()


async def run_worker_once(sm: async_sessionmaker[AsyncSession]) -> bool:
    async with session_scope(sm) as db:
        # Восстанавливаем зависшие задачи перед попыткой взять новую
        ttl = int(os.getenv("AI_JOB_STUCK_TTL", "3600"))
        try:
            await recover_stuck_generation_jobs(db, ttl_seconds=ttl)
        except Exception:
            logger.exception("recover_stuck_generation_jobs failed")
        processed = await process_next_generation_job(db)
        return processed is not None


async def _worker_loop(sm, poll_interval: float, oneshot: bool):
    while True:
        try:
            has_job = await run_worker_once(sm)
            if not has_job:
                await asyncio.sleep(poll_interval)
            else:
                await asyncio.sleep(0.1)
        except Exception:
            logger.exception("Worker iteration failed")
            await asyncio.sleep(1.0)
        if oneshot:
            break


async def run_worker_loop(poll_interval: float = 2.0):
    """Основной цикл: конкурентная обработка задач.
    AI_WORKER_CONCURRENCY — число параллельных воркеров (по умолчанию 1).
    AI_WORKER_ONESHOT=true — один прогон на воркер.
    """
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))
    sm = _make_sessionmaker()
    oneshot = (os.getenv("AI_WORKER_ONESHOT") or "").lower() in ("1", "true", "yes")
    try:
        concurrency = int(os.getenv("AI_WORKER_CONCURRENCY", "1"))
    except Exception:
        concurrency = 1
    concurrency = max(1, concurrency)

    if concurrency == 1:
        await _worker_loop(sm, poll_interval, oneshot)
        return

    tasks = []
    for i in range(concurrency):
        # небольшое рассинхронизирующее смещение старта
        await asyncio.sleep(0.05 * i)
        tasks.append(asyncio.create_task(_worker_loop(sm, poll_interval, oneshot)))
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
