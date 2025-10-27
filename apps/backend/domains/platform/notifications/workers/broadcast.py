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
        except (RuntimeError, ValueError, ConnectionError) as exc:
            self.logger.exception("broadcast worker tick failed", exc_info=exc)
            worker_metrics.inc("failed")
            return

        if not summaries:
            await self._run_retention()
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

        await self._run_retention()

    async def _run_retention(self) -> None:
        settings = getattr(self._container, "settings", None)
        repo = getattr(self._container, "repo", None)
        if repo is None:
            return
        retention_service = getattr(self._container, "retention_service", None)
        retention_days = None
        max_per_user = None
        if retention_service is not None:
            try:
                config = await retention_service.get_config()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.exception(
                    "notifications retention config load failed", exc_info=exc
                )
                config = None
            if isinstance(config, dict):
                retention_days = config.get("retention_days")
                max_per_user = config.get("max_per_user")
        if retention_days is None or max_per_user is None:
            if settings:
                retention_days = retention_days or getattr(
                    settings.notifications, "retention_days", None
                )
                max_per_user = max_per_user or getattr(
                    settings.notifications, "max_per_user", None
                )
        if retention_days in {None, 0} and max_per_user in {None, 0}:
            return
        try:
            result = await repo.prune(
                retention_days=retention_days,
                max_per_user=max_per_user,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("notifications retention failed", exc_info=exc)
            worker_metrics.inc("failed")
            return
        worker_metrics.inc("retention_runs")
        worker_metrics.inc(
            "retention_removed_age", int(result.get("removed_by_age", 0))
        )
        worker_metrics.inc(
            "retention_removed_limit", int(result.get("removed_by_limit", 0))
        )
        worker_metrics.inc(
            "retention_removed_messages", int(result.get("removed_messages", 0))
        )
        total_removed = int(result.get("removed_by_age", 0)) + int(
            result.get("removed_by_limit", 0)
        )
        if total_removed or result.get("removed_messages"):
            self.logger.info(
                "notifications retention cleaned rows=%s age=%s limit=%s messages=%s",
                total_removed,
                int(result.get("removed_by_age", 0)),
                int(result.get("removed_by_limit", 0)),
                int(result.get("removed_messages", 0)),
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
