"""Minimal request logging middleware for tests."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

# Dedicated logger name used in tests and production
logger = logging.getLogger("app.http")
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        logger.info("%s %s %s", request.method, request.url.path, response.status_code)
        return response
