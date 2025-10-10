from __future__ import annotations

from typing import Any


class HomeConfigError(RuntimeError):
    """Base error for home configuration domain."""


class HomeConfigRepositoryError(HomeConfigError):
    pass


class HomeConfigNotFound(HomeConfigError):
    pass


class HomeConfigDraftNotFound(HomeConfigError):
    pass


class HomeConfigValidationError(HomeConfigError):
    def __init__(self, code: str, *, details: Any | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.details = details


class HomeConfigSchemaError(HomeConfigValidationError):
    pass


class HomeConfigDuplicateBlockError(HomeConfigValidationError):
    pass


__all__ = [
    "HomeConfigDraftNotFound",
    "HomeConfigDuplicateBlockError",
    "HomeConfigError",
    "HomeConfigNotFound",
    "HomeConfigRepositoryError",
    "HomeConfigSchemaError",
    "HomeConfigValidationError",
]
