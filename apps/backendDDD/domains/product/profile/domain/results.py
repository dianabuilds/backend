from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileView:
    id: str
    username: str
    bio: str | None = None
