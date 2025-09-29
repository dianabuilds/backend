from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import cast

import pytest

from domains.platform.notifications.application.broadcast_orchestrator import (
    BroadcastDeliverySummary,
)
from domains.platform.notifications.domain.broadcast import BroadcastStatus
from domains.platform.notifications.workers.broadcast import (
    _WORKER_NAME,
    _BroadcastWorker,
)
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics
from packages.core.config import Settings
from packages.worker.registry import WorkerRuntimeContext


class _StubOrchestrator:
    def __init__(self, summaries):
        self._summaries = summaries
        self.calls: list[int] = []

    async def process_due(self, *, limit: int) -> list[BroadcastDeliverySummary]:
        self.calls.append(limit)
        return list(self._summaries)


class _StubContainer:
    def __init__(self, orchestrator: _StubOrchestrator) -> None:
        self.orchestrator = orchestrator


def _reset_worker_metrics() -> None:
    worker_metrics.counters.clear()
    worker_metrics.counters.update({"started": 0, "completed": 0, "failed": 0})
    worker_metrics.duration_sum_ms = 0.0
    worker_metrics.duration_count = 0
    worker_metrics.cost_usd_total = 0.0
    worker_metrics.tokens_prompt_total = 0
    worker_metrics.tokens_completion_total = 0
    worker_metrics.stage_counts.clear()
    worker_metrics.stage_duration_sum_ms.clear()


@pytest.mark.asyncio
async def test_broadcast_worker_updates_metrics() -> None:
    _reset_worker_metrics()
    summaries = [
        BroadcastDeliverySummary(
            broadcast_id="b-1",
            status=BroadcastStatus.SENT,
            total=10,
            sent=10,
            failed=0,
        ),
        BroadcastDeliverySummary(
            broadcast_id="b-2",
            status=BroadcastStatus.FAILED,
            total=5,
            sent=3,
            failed=2,
        ),
    ]
    orchestrator = _StubOrchestrator(summaries)

    def _factory(context: WorkerRuntimeContext) -> _StubContainer:
        return _StubContainer(orchestrator)

    settings = cast(Settings, SimpleNamespace())
    ctx = WorkerRuntimeContext(
        settings=settings,
        env={},
        logger=logging.getLogger("test.broadcast.worker"),
    )
    worker = _BroadcastWorker(
        context=ctx,
        interval=1.0,
        jitter=0.0,
        batch_limit=5,
        immediate=False,
        container_factory=_factory,
    )

    await worker._run_tick()

    assert orchestrator.calls == [5]
    assert worker_metrics.counters["started"] == 2
    assert worker_metrics.counters["completed"] == 1
    assert worker_metrics.counters["failed"] == 1
    assert worker_metrics.duration_count == 2
    assert worker_metrics.stage_counts.get(_WORKER_NAME) == 2

    await worker.shutdown()
