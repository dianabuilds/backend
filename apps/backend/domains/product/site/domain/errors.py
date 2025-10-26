from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SiteRepositoryError(RuntimeError):
    """Base persistence error for the site editor."""


class SitePageNotFound(SiteRepositoryError):
    """Raised when a page cannot be found."""


class SitePageVersionNotFound(SiteRepositoryError):
    """Raised when a requested version is missing."""


class SiteUnauthorizedError(SiteRepositoryError):
    """Raised when an operation is not allowed for the current user."""


class SiteValidationError(RuntimeError):
    """Raised when draft validation fails."""

    def __init__(
        self,
        code: str,
        *,
        general: list[Mapping[str, Any]],
        blocks: Mapping[str, list[Mapping[str, Any]]],
    ) -> None:
        super().__init__(code)
        self.code = code
        self.general_errors = list(general)
        self.block_errors = {block: list(errors) for block, errors in blocks.items()}


__all__ = [
    "SiteRepositoryError",
    "SitePageNotFound",
    "SitePageVersionNotFound",
    "SiteUnauthorizedError",
    "SiteValidationError",
]
