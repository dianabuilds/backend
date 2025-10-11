from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar, cast

logger = logging.getLogger("apps/backend")

F = TypeVar("F", bound=Callable[..., Any])


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )


def _log_duration(name: str, started_at: float) -> None:
    try:
        dt = (time.perf_counter() - started_at) * 1000.0
        logger.info("trace %s %.2fms", name, dt)
    except Exception as exc:
        logger.debug("trace logging failed for %s", name, exc_info=exc)


def _log_error(name: str) -> None:
    try:
        logger.exception("trace.error %s", name)
    except Exception as exc:
        logger.debug("trace logging failed for %s", name, exc_info=exc)


def _is_async_callable(fn: Callable[..., Any]) -> bool:
    if asyncio.iscoroutinefunction(fn):
        return True
    if callable(fn):
        try:
            call_attr = type(fn).__call__
        except AttributeError:
            return False
        return asyncio.iscoroutinefunction(call_attr)
    return False


def with_trace(fn: F) -> F:
    """Lightweight tracing decorator: logs duration and errors.

    Safe no-op if logging is not configured; avoids raising exceptions.
    """

    name = getattr(fn, "__qualname__", getattr(fn, "__name__", "fn"))

    if _is_async_callable(fn):
        async_fn = cast(Callable[..., Awaitable[Any]], fn)

        @wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            started_at = time.perf_counter()
            try:
                return await async_fn(*args, **kwargs)
            except Exception:
                _log_error(name)
                raise
            finally:
                _log_duration(name, started_at)

        return cast(F, async_wrapper)

    call_fn = cast(Callable[..., Any], fn)

    @wraps(fn)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        started_at = time.perf_counter()
        try:
            return call_fn(*args, **kwargs)
        except Exception:
            _log_error(name)
            raise
        finally:
            _log_duration(name, started_at)

    return cast(F, sync_wrapper)
