from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    async def send(
        self,
        to: list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
    ) -> None: ...


__all__ = ["EmailSender"]
