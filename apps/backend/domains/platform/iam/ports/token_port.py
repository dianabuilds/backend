from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str | None = None


class TokenPort(Protocol):
    def issue(
        self, subject: str, claims: Mapping[str, Any] | None = None
    ) -> TokenPair: ...
    def refresh(self, refresh_token: str) -> TokenPair: ...


__all__ = ["TokenPort", "TokenPair"]
