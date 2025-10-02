from __future__ import annotations

"""Domain-specific exceptions for AI provider interactions."""


class ProviderError(RuntimeError):
    """Raised when an AI provider request fails."""

    def __init__(self, message: str, *, code: str = "provider_error") -> None:
        super().__init__(message)
        self.code = code


__all__ = ["ProviderError"]
