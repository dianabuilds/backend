from __future__ import annotations

import logging
import time
from collections.abc import Callable

logger = logging.getLogger("apps/backend")


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )


def with_trace(fn: Callable[..., object]) -> Callable[..., object]:
    """Lightweight tracing decorator: logs duration and errors.

    Safe no-op if logging is not configured; avoids raising exceptions.
    """

    def wrapper(*args: object, **kwargs: object) -> object:
        name = getattr(fn, "__qualname__", getattr(fn, "__name__", "fn"))
        t0 = time.perf_counter()
        try:
            res = fn(*args, **kwargs)
            return res
        except Exception:
            try:
                logger.warning("trace.error %s", name, exc_info=True)
            except Exception:
                pass
            raise
        finally:
            try:
                dt = (time.perf_counter() - t0) * 1000.0
                logger.info("trace %s %.2fms", name, dt)
            except Exception:
                pass

    return wrapper
