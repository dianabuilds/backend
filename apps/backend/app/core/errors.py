from __future__ import annotations

from typing import Any, Optional


class DomainError(Exception):
    """Base application-level exception."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
