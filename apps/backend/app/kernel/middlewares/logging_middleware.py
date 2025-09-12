"""Minimal request logging middleware for tests and production."""

from __future__ import annotations

import logging
import random
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.kernel.config import settings

logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = perf_counter()
        response: Response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000
        level_name = (settings.logging.request_level or "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        if duration_ms >= settings.logging.slow_request_ms:
            level = logging.WARNING
        else:
            try:
                rate = float(getattr(settings.logging, "sampling_rate_debug", 0.0) or 0.0)
            except Exception:
                rate = 0.0
            if rate > 0.0:
                try:
                    if random.random() < rate:
                        level = logging.DEBUG
                except Exception:
                    pass
        logger.log(level, "%s %s %s", request.method, request.url.path, response.status_code)
        return response


__all__ = ["RequestLoggingMiddleware"]
