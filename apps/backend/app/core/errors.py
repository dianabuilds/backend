from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class DomainError(Exception):
    """Base application-level exception."""

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


# Map HTTP status codes to our unified error codes. Keep this list small and
# predictable so clients can rely on a limited set of error codes.
ERROR_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
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
    """Return ``HTTPException`` with a unified error response body.

    Parameters
    ----------
    status_code: int
        HTTP status code to return.
    message: str
        Human readable error message.
    code: str, optional
        Application specific error code. If omitted, a default code is inferred
        from ``status_code``.
    details: Any, optional
        Optional structured details to include under ``error.details``.
    """

    if code is None:
        code = ERROR_CODE_MAP.get(status_code, "HTTP_ERROR")

    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return HTTPException(status_code=status_code, detail=body)


__all__ = ["DomainError", "http_error", "ERROR_CODE_MAP"]
