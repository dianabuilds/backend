from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class AuthIdentity:
    id: str
    email: str | None
    username: str | None
    role: str
    is_active: bool


class CredentialsPort(Protocol):
    async def authenticate(self, login: str, password: str) -> AuthIdentity | None:
        """Validate credentials and return identity info if matched."""


__all__ = ["CredentialsPort", "AuthIdentity"]
