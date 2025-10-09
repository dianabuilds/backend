from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import partial
from typing import Any, Protocol, cast, runtime_checkable

from fastapi import FastAPI
from starlette.applications import Starlette

logger = logging.getLogger(__name__)


@runtime_checkable
class _Stoppable(Protocol):
    def stop(self) -> None: ...


ShutdownHook = Callable[[], Awaitable[None]]


async def start_events_relay(app: FastAPI, *, block_ms: int = 5000) -> ShutdownHook:
    """Launch the synchronous events relay in an executor-managed task.

    Returns a coroutine that stops the relay gracefully on application shutdown.
    """

    sapp = cast(Starlette, app)
    container: Any | None = getattr(sapp.state, "container", None)
    if container is None:
        logger.warning("Events relay not started: container is missing")

        async def _noop() -> None:
            return None

        return _noop

    events = getattr(container, "events", None)
    if events is None:
        logger.info("Events relay not started: container has no events bus")

        async def _noop() -> None:
            return None

        return _noop

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    runner = partial(events.run, block_ms=block_ms)

    async def _relay_worker() -> None:
        backoff = 1.0
        while not stop_event.is_set():
            try:
                await loop.run_in_executor(None, runner)
                return
            except asyncio.CancelledError:
                logger.info("Events relay task cancelled")
                raise
            except Exception as exc:
                if stop_event.is_set():
                    logger.debug("Events relay stopping after failure")
                    return
                logger.exception(
                    "Events relay crashed; retrying in %.1fs", backoff, exc_info=exc
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, 30.0)

    task = asyncio.create_task(_relay_worker(), name="events-relay")

    async def _shutdown() -> None:
        if stop_event.is_set():
            return
        stop_event.set()
        bus = getattr(events, "bus", None)
        if isinstance(bus, _Stoppable):
            try:
                bus.stop()
            except Exception as exc:
                logger.exception("Failed to stop events relay bus", exc_info=exc)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Events relay task raised during shutdown", exc_info=exc)

    return _shutdown
