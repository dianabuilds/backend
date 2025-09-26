from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from domains.platform.flags.wires import build_container as build_flags_container
from domains.platform.notifications.domain.broadcast import BroadcastStatus
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics
from packages.core.db import dispose_async_engines
from packages.worker import PeriodicWorker, PeriodicWorkerConfig
from packages.worker.registry import WorkerRuntimeContext, register_worker

from ..wires import build_container

_WORKER_NAME = "notifications.broadcast"


def _env_float(env: dict[str, str], key: str, default: float) -> float:
    try:
        return float(env.get(key, default))
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return default


def _env_int(env: dict[str, str], key: str, default: int) -> int:
    try:
        return int(env.get(key, default))
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return default


class _BroadcastWorker(PeriodicWorker):
    def __init__(
        self,
        *,
        context: WorkerRuntimeContext,
        interval: float,
        jitter: float,
        batch_limit: int,
        immediate: bool,
        container_factory: Callable[[WorkerRuntimeContext], Any] | None = None,
    ) -> None:
        factory = container_factory or self._default_container_factory
        container = factory(context)
        orchestrator = getattr(container, "orchestrator", None)
        if orchestrator is None:
            raise RuntimeError("notifications container missing orchestrator")
        self._orchestrator = orchestrator
        self._batch_limit = max(1, int(batch_limit))

        async def _tick() -> None:
            await self._run_tick()

        config = PeriodicWorkerConfig(
            interval=interval,
            jitter=jitter,
            immediate=immediate,
        )
        super().__init__(_WORKER_NAME, _tick, config=config, logger=context.logger)
        self._container = container

    @staticmethod
    def _default_container_factory(ctx: WorkerRuntimeContext):
        flags = build_flags_container(settings=ctx.settings)
        return build_container(settings=ctx.settings, flag_service=flags.service)

    async def _run_tick(self) -> None:
        started_at = perf_counter()
        try:
            summaries = await self._orchestrator.process_due(limit=self._batch_limit)
        except Exception:
            self.logger.exception("broadcast worker tick failed")
            worker_metrics.inc("failed")
            return

        if not summaries:
            return

        elapsed_ms = max((perf_counter() - started_at) * 1000.0, 0.0)
        per_summary_ms = elapsed_ms / max(len(summaries), 1)

        worker_metrics.inc("started", len(summaries))
        for summary in summaries:
            worker_metrics.observe_duration(per_summary_ms)
            worker_metrics.observe_stage(_WORKER_NAME, per_summary_ms)
            if summary.status is BroadcastStatus.SENT:
                worker_metrics.inc("completed")
            else:
                worker_metrics.inc("failed")
            self.logger.info(
                "broadcast %s completed status=%s total=%s sent=%s failed=%s",
                summary.broadcast_id,
                summary.status.value,
                summary.total,
                summary.sent,
                summary.failed,
            )

    async def shutdown(self) -> None:
        await dispose_async_engines()
        await super().shutdown()


@register_worker(_WORKER_NAME)
async def build_broadcast_worker(context: WorkerRuntimeContext):
    env = dict(context.env)
    interval = _env_float(env, "NOTIFICATIONS_BROADCAST_INTERVAL", 30.0)
    jitter = _env_float(env, "NOTIFICATIONS_BROADCAST_JITTER", 5.0)
    batch_limit = max(1, _env_int(env, "NOTIFICATIONS_BROADCAST_BATCH_LIMIT", 5))
    immediate = env.get("NOTIFICATIONS_BROADCAST_IMMEDIATE", "1") not in {
        "0",
        "false",
        "False",
    }
    return _BroadcastWorker(
        context=context,
        interval=interval,
        jitter=jitter,
        batch_limit=batch_limit,
        immediate=immediate,
    )


__all__ = ["build_broadcast_worker"]
