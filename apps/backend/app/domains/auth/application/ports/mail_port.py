from __future__ import annotations

from typing import Protocol


class IMailer(Protocol):
    async def send_verification(self, email: str, token: str) -> None:  # pragma: no cover
        ...

    async def send_reset_password(self, email: str, token: str) -> None:  # pragma: no cover
        ...
