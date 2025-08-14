"""Minimal request logging middleware for tests."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        logger.info("Request %s %s", request.method, request.url.path)
        response: Response = await call_next(request)
        logger.info("Response %s %s", request.method, request.url.path)
        return response
