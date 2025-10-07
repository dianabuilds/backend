from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

log = logging.getLogger(__name__)


def with_retry(
    attempts: int = 3,
    backoff: float = 0.1,
    *,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
    logger: logging.Logger | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry decorator for notification operations with exponential backoff."""

    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    retry_log = logger or log

    def deco(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def inner(*a: P.args, **kw: P.kwargs) -> R:
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*a, **kw)
                except retry_exceptions as exc:
                    if attempt >= attempts:
                        retry_log.error(
                            "notifications retry exhausted after %s attempts: %s",
                            attempts,
                            exc,
                            exc_info=exc,
                        )
                        raise
                    retry_log.warning(
                        "notifications retry attempt %s/%s failed: %s",
                        attempt,
                        attempts,
                        exc,
                        exc_info=exc,
                    )
                    sleep(max(0.0, backoff) * (2 ** (attempt - 1)))
            raise RuntimeError("retry loop exited without returning")

        return inner

    return deco
