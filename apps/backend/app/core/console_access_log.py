from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ConsoleAccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware printing simple access logs to stdout."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        print(f"HTTP {request.method} {request.url.path} -> {response.status_code}")
        return response
