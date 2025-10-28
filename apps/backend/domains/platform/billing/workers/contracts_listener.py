from __future__ import annotations

from collections.abc import Callable
from typing import Any

from domains.platform.billing.wires import build_container as build_billing_container
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics
from packages.core.db import dispose_async_engines
from packages.worker import PeriodicWorker, PeriodicWorkerConfig
from packages.worker.registry import WorkerRuntimeContext, register_worker

_WORKER_NAME = "billing.contracts"


class _ContractsWorker(PeriodicWorker):
    def __init__(
        self,
        *,
        context: WorkerRuntimeContext,
        interval: float,
        jitter: float,
        batch_limit: int,
        container_factory: Callable[[WorkerRuntimeContext], Any] | None = None,
    ) -> None:
        factory = container_factory or self._default_container_factory
        container = factory(context)
        self._service = container.service
        self._batch_limit = max(1, int(batch_limit))

        async def _tick() -> None:
            await self._run_tick()

        config = PeriodicWorkerConfig(
            interval=interval,
            jitter=jitter,
            immediate=True,
        )
        super().__init__(_WORKER_NAME, _tick, config=config, logger=context.logger)
        self._container = container

    @staticmethod
    def _default_container_factory(ctx: WorkerRuntimeContext):
        return build_billing_container(settings=ctx.settings)

    async def _run_tick(self) -> None:
        try:
            result = await self._service.reconcile_pending_transactions(
                older_than_seconds=120,
                limit=self._batch_limit,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception(
                "billing contracts worker tick failed",
                exc_info=exc,
                extra={"worker": _WORKER_NAME, "batch_limit": self._batch_limit},
            )
            worker_metrics.inc("failed")
            return
        processed = int(result.get("count", 0))
        if processed:
            worker_metrics.inc("completed", processed)
        else:
            worker_metrics.inc("idle")
        self.logger.debug(
            "billing contracts worker processed pending=%s",
            processed,
            extra={"worker": _WORKER_NAME, "processed": processed},
        )

    async def shutdown(self) -> None:
        await dispose_async_engines()
        await super().shutdown()


@register_worker(_WORKER_NAME)
async def build_billing_contracts_worker(context: WorkerRuntimeContext):
    env = dict(context.env)
    interval = float(env.get("BILLING_CONTRACTS_INTERVAL", 30.0))
    jitter = float(env.get("BILLING_CONTRACTS_JITTER", 5.0))
    batch_limit = int(env.get("BILLING_CONTRACTS_BATCH_LIMIT", 50))
    return _ContractsWorker(
        context=context,
        interval=max(interval, 5.0),
        jitter=max(jitter, 0.0),
        batch_limit=max(batch_limit, 1),
    )


__all__ = ["build_billing_contracts_worker"]
