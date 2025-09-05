"""Minimal request logging middleware for tests."""

from __future__ import annotations

import logging
from time import perf_counter

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
        level = logging.INFO
        if duration_ms >= settings.logging.slow_request_ms:
            level = logging.WARNING
        logger.log(level, "%s %s %s", request.method, request.url.path, response.status_code)
        return response
