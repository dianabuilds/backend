from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class DomainError(Exception):
    """Base application-level exception for domain and application layers."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


# Map HTTP status codes to unified error codes used across the app.
ERROR_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def http_error(
    status_code: int,
    message: str,
    *,
    code: str | None = None,
    details: Any | None = None,
) -> HTTPException:
    """Return HTTPException with a unified error response body."""

    if code is None:
        code = ERROR_CODE_MAP.get(status_code, "HTTP_ERROR")

    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return HTTPException(status_code=status_code, detail=body)


__all__ = ["DomainError", "http_error", "ERROR_CODE_MAP"]

