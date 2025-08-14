from __future__ import annotations

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.log_filters import request_id_var, ip_var, ua_var

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Extract or generate correlation id and store in context vars."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        ip_var.set(request.client.host if request.client else None)
        ua_var.set(request.headers.get("user-agent"))
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-Id"] = request_id
        return response
