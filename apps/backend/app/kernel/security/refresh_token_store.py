from __future__ import annotations

from typing import Protocol


class RefreshTokenStore(Protocol):
    """Protocol describing refresh token persistence."""

    def set(self, jti: str, sub: str) -> None:  # pragma: no cover - interface
        ...

    def pop(self, jti: str) -> str | None:  # pragma: no cover - interface
        ...


class MemoryRefreshTokenStore:
    """Simple in-memory store for refresh tokens.

    Intended for tests and single-process deployments. Replace with a
    distributed store (e.g. Redis) by providing an object that satisfies
    :class:`RefreshTokenStore`.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def set(self, jti: str, sub: str) -> None:
        self._store[jti] = sub

    def pop(self, jti: str) -> str | None:
        return self._store.pop(jti, None)


__all__ = ["RefreshTokenStore", "MemoryRefreshTokenStore"]

