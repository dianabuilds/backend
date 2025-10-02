import logging
import time
from types import SimpleNamespace

import fakeredis.aioredis
import pytest

from domains.platform.telemetry.adapters.rum_repository import RumRedisRepository
from domains.platform.telemetry.workers import rum_rollup
from packages.core.config import Settings
from packages.worker.registry import WorkerRuntimeContext


class _DummyExporter:
    def __init__(self) -> None:
        self.records: list[dict] | None = None
        self.bucket = "rum-test"

    async def export(self, records):
        self.records = list(records)
        return "rum/test.jsonl"


@pytest.mark.asyncio
async def test_rum_rollup_worker_flushes_pending(monkeypatch) -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RumRedisRepository(fake)

    now_ms = int(time.time() * 1000) - 3 * 60_000
    await repo.add(
        {
            "event": "navigation",
            "ts": now_ms,
            "url": "https://app.local/home",
            "data": {"ttfb": 200.0, "loadEvent": 500.0},
        }
    )

    settings = Settings()
    context = WorkerRuntimeContext(
        settings=settings, env={}, logger=logging.getLogger("test.rum.worker")
    )
    monkeypatch.setattr(
        rum_rollup,
        "build_container",
        lambda settings: SimpleNamespace(rum_repository=repo, settings=settings),
    )

    worker = rum_rollup.RumRollupWorker(
        context=context,
        interval=0.1,
        jitter=0.0,
        min_age_sec=60.0,
        batch_size=50,
    )
    dummy = _DummyExporter()
    worker._exporter = dummy  # type: ignore[attr-defined]

    await worker._run_once()

    assert dummy.records is not None
    record = dummy.records[0]
    assert record["event"] == "navigation"
    assert record["metrics"]["ttfb"]["avg"] == pytest.approx(200.0)
    assert record["metrics"]["loadEvent"]["sum"] == pytest.approx(500.0)

    pending = await repo.fetch_pending_aggregates(rum_rollup._now_ms())
    assert pending == []
