from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable
from typing import Any, TypeVar

_T = TypeVar("_T")

_LOOP_LOCK = threading.Lock()
_BACKGROUND_LOOP: asyncio.AbstractEventLoop | None = None
_BACKGROUND_THREAD: threading.Thread | None = None


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


def run_sync(coro: Awaitable[_T], *, loop: asyncio.AbstractEventLoop | None = None) -> _T:
    """Execute an async coroutine on a background event loop synchronously."""

    target_loop = loop or _ensure_background_loop()
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None
    if running_loop is target_loop:
        raise RuntimeError("run_sync cannot be called from the managed background loop")
    future = asyncio.run_coroutine_threadsafe(coro, target_loop)
    return future.result()


def submit_async(coro: Awaitable[Any], *, loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Schedule a coroutine on the background loop without waiting for completion."""

    target_loop = loop or _ensure_background_loop()
    asyncio.run_coroutine_threadsafe(coro, target_loop)


__all__ = ["run_sync", "submit_async"]
