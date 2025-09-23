from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class AppError(Exception):
    """Base error for application-specific exceptions."""


class ApiError(AppError):
    """Structured API error with machine-readable code."""

    def __init__(
        self,
        code: str,
        status_code: int,
        message: str | None = None,
        *,
        extra: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.status_code = int(status_code)
        self.message = message
        self.extra = dict(extra or {})
        self.headers = dict(headers or {})
        if retry_after is not None and "Retry-After" not in self.headers:
            self.headers["Retry-After"] = str(retry_after)


class NotFound(AppError):
    pass


class Conflict(AppError):
    pass


class PolicyDenied(AppError):
    pass


__all__ = [
    "AppError",
    "ApiError",
    "NotFound",
    "Conflict",
    "PolicyDenied",
]
