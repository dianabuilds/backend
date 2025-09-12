from __future__ import annotations

from typing import Protocol


class ITokenService(Protocol):
    def create_access_token(self, user_id) -> str:  # pragma: no cover - контракт
        ...

    async def create_refresh_token(self, user_id) -> str:  # pragma: no cover - контракт
        ...

    def verify_access_token(self, token: str) -> str | None:  # pragma: no cover - контракт
        ...

    async def verify_refresh_token(self, token: str) -> str | None:  # pragma: no cover - контракт
        ...
