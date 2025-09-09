"""Minimal request logging middleware for tests."""

from __future__ import annotations

import logging
from time import perf_counter
import random

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# Dedicated logger name used in tests and production
logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and responses.

    The middleware measures the request processing time and promotes slow
    requests (longer than ``settings.logging.slow_request_ms``) to
    ``WARNING`` level.  This behaviour is relied upon by tests checking the
    slow request threshold.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = perf_counter()
        response: Response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000
        # Base level from settings
        level_name = (settings.logging.request_level or "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        # Promote slow requests to WARNING (tests rely on this behaviour)
        if duration_ms >= settings.logging.slow_request_ms:
            level = logging.WARNING
        else:
            # Sample some non-slow requests down to DEBUG to reduce noise
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
