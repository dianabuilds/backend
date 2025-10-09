"""Exceptions for admin node use-cases."""

from __future__ import annotations


class AdminQueryError(Exception):
    """Domain-level error for admin queries."""

    def __init__(
        self, status_code: int, detail: str, *, cause: Exception | None = None
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        if cause is not None:
            self.__cause__ = cause


__all__ = ["AdminQueryError"]
