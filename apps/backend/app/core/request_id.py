from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.log_filters import (
    account_id_var,
    ip_var,
    request_id_var,
    ua_var,
    workspace_id_var,
)

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
        workspace_id = request.query_params.get("workspace_id")
        if not workspace_id and hasattr(request.state, "preview_token"):
            workspace_id = request.state.preview_token.get("workspace_id")
        workspace_token = workspace_id_var.set(workspace_id)
        account_token = account_id_var.set(workspace_id)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(token)
            workspace_id_var.reset(workspace_token)
            account_id_var.reset(account_token)
        response.headers["X-Request-Id"] = request_id
        return response
