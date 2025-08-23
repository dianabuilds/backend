from __future__ import annotations

from typing import Protocol


class ITokenService(Protocol):
    def create_access_token(self, subject: str) -> str:  # pragma: no cover
        ...

    def create_refresh_token(self, subject: str) -> str:  # pragma: no cover
        ...

    def verify_access_token(self, token: str) -> str | None:  # pragma: no cover
        ...
