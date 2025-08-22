from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthTokens:
    access: str
    refresh: str
