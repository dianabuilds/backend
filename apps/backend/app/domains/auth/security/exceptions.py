from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthError(Exception):
    """Base class for authentication/authorization errors."""

    message: str = ""
    user_id: str | None = None
    role: str | None = None

    @property
    def code(self) -> str:  # pragma: no cover - overridden in subclasses
        return "AUTH_ERROR"

    @property
    def status_code(self) -> int:  # pragma: no cover - overridden
        return 401


class AuthRequiredError(AuthError):
    message = "Authorization header missing"

    @property
    def code(self) -> str:
        return "AUTH_REQUIRED"


class InvalidTokenError(AuthError):
    message = "Invalid authentication token"

    @property
    def code(self) -> str:
        return "INVALID_TOKEN"


class TokenExpiredError(AuthError):
    message = "Token has expired"

    @property
    def code(self) -> str:
        return "TOKEN_EXPIRED"


class ForbiddenError(AuthError):
    message = "Forbidden"

    @property
    def code(self) -> str:
        return "FORBIDDEN"

    @property
    def status_code(self) -> int:
        return 403

__all__ = [
    "AuthError",
    "AuthRequiredError",
    "InvalidTokenError",
    "TokenExpiredError",
    "ForbiddenError",
]

