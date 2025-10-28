from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.workers.contracts_listener import (
    _ContractsWorker,
)
from packages.worker.registry import WorkerRuntimeContext


@pytest.mark.asyncio
async def test_contracts_worker_tick_calls_service() -> None:
    context = WorkerRuntimeContext(
        settings=SimpleNamespace(),
        env={},
        logger=SimpleNamespace(
            debug=lambda *args, **kwargs: None,
            exception=lambda *args, **kwargs: None,
            info=lambda *args, **kwargs: None,
        ),
    )
    service = SimpleNamespace(
        reconcile_pending_transactions=AsyncMock(return_value={"count": 2})
    )
    container = SimpleNamespace(service=service)

    worker = _ContractsWorker(
        context=context,
        interval=5.0,
        jitter=0.0,
        batch_limit=50,
        container_factory=lambda _ctx: container,
    )

    await worker._run_tick()
    service.reconcile_pending_transactions.assert_awaited_once()
