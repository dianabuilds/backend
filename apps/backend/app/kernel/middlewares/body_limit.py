from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.kernel.config import settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple request body size limit based on Content-Length.
    If the header is missing (chunked), the limit is not applied.
    """

    def __init__(self, app, max_bytes: int | None = None):
        super().__init__(app)
        default_limit = 2 * 1024 * 1024
        security = getattr(settings, "security", None)
        configured = getattr(security, "max_request_body_bytes", None) if security else None
        self.max_bytes = int(max_bytes or configured or default_limit)

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            cl = request.headers.get("nodes-length")
            if cl:
                try:
                    length = int(cl)
                except ValueError:
                    length = None
                if length is not None and length > self.max_bytes:
                    return JSONResponse({"detail": "Request body too large"}, status_code=413)
        return await call_next(request)


__all__ = ["BodySizeLimitMiddleware"]
