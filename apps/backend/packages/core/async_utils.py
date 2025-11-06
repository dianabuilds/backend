from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any, TypeVar

try:
    import anyio
except ImportError:  # pragma: no cover - optional dependency
    anyio = None  # type: ignore[assignment]

_T = TypeVar("_T")

_LOOP_LOCK = threading.Lock()
_BACKGROUND_LOOP: asyncio.AbstractEventLoop | None = None
_BACKGROUND_THREAD: threading.Thread | None = None
_THREAD_STATE = threading.local()


async def _probe_anyio_worker() -> bool:
    return True


def _in_anyio_worker() -> bool:
    if anyio is None:
        return False
    cached = getattr(_THREAD_STATE, "anyio_worker", None)
    if cached is not None:
        return bool(cached)
    try:
        anyio.from_thread.run(_probe_anyio_worker)
    except RuntimeError as exc:
        message = str(exc)
        if message == "This function can only be run from an AnyIO worker thread":
            cached = False
        elif "Not running inside an AnyIO worker thread" in message:
            cached = False
        else:
            raise
    else:
        cached = True
    _THREAD_STATE.anyio_worker = cached
    return bool(cached)


def _ensure_background_loop() -> asyncio.AbstractEventLoop:
    global _BACKGROUND_LOOP, _BACKGROUND_THREAD
    if _BACKGROUND_LOOP and _BACKGROUND_LOOP.is_running():
        return _BACKGROUND_LOOP
    with _LOOP_LOCK:
        if _BACKGROUND_LOOP and _BACKGROUND_LOOP.is_running():
            return _BACKGROUND_LOOP
        loop = asyncio.new_event_loop()
        ready = threading.Event()

        def _runner() -> None:
            asyncio.set_event_loop(loop)
            ready.set()
            loop.run_forever()

        thread = threading.Thread(target=_runner, name="core-async-loop", daemon=True)
        thread.start()
        ready.wait()
        _BACKGROUND_LOOP = loop
        _BACKGROUND_THREAD = thread
        return loop


def run_sync(
    coro: Coroutine[Any, Any, _T], *, loop: asyncio.AbstractEventLoop | None = None
) -> _T:
    """Execute an async coroutine on a background event loop synchronously."""

    if loop is None and _in_anyio_worker():

        async def _runner() -> _T:
            return await coro

        return anyio.from_thread.run(_runner)

    target_loop = loop or _ensure_background_loop()
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None
    if running_loop is target_loop:
        raise RuntimeError("run_sync cannot be called from the managed background loop")
    future: Future[_T] = asyncio.run_coroutine_threadsafe(coro, target_loop)
    return future.result()


def submit_async(
    coro: Coroutine[Any, Any, Any], *, loop: asyncio.AbstractEventLoop | None = None
) -> None:
    """Schedule a coroutine on the background loop without waiting for completion."""

    if loop is None and _in_anyio_worker():

        def _schedule() -> None:
            asyncio.get_running_loop().create_task(coro)

        anyio.from_thread.run_sync(_schedule)
        return

    target_loop = loop or _ensure_background_loop()
    asyncio.run_coroutine_threadsafe(coro, target_loop)


__all__ = ["run_sync", "submit_async"]
