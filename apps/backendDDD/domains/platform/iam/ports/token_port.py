from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str | None = None


class TokenPort(Protocol):
    def issue(self, subject: str) -> TokenPair: ...
    def refresh(self, refresh_token: str) -> TokenPair: ...


__all__ = ["TokenPort", "TokenPair"]
