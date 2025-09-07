from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.log_filters import (
    account_id_var,
    ip_var,
    profile_id_var,
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
        # Prefer explicit profile-centric id; accept legacy names for compatibility
        profile_id = (
            request.headers.get("X-Profile-Id")
            or request.query_params.get("profile_id")
        )
        account_id = (
            request.headers.get("X-Account-Id")
            or request.query_params.get("account_id")
        )
        if not (profile_id or account_id) and hasattr(request.state, "preview_token"):
            account_id = request.state.preview_token.get("workspace_id")

        # Normalize: prefer profile_id; mirror to legacy vars for logs/compat
        effective_id = profile_id or account_id

        # Store in request state for downstream handlers
        try:
            request.state.profile_id = profile_id
            request.state.account_id = effective_id
        except Exception:
            pass
        # For backward-compatible logs, mirror the same value to workspace_id/account_id
        workspace_token = workspace_id_var.set(effective_id)
        account_token = account_id_var.set(effective_id)
        profile_token = profile_id_var.set(profile_id or effective_id)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(token)
            workspace_id_var.reset(workspace_token)
            account_id_var.reset(account_token)
            profile_id_var.reset(profile_token)
        response.headers["X-Request-Id"] = request_id
        return response
