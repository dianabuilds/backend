from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: str
    email: str | None
    wallet_address: str | None
    is_active: bool
    role: str
    username: str | None
    created_at: datetime


__all__ = ["User"]
