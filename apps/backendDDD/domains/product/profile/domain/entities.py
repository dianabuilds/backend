from __future__ import annotations

from dataclasses import dataclass

from .policies import validate_username


@dataclass
class Profile:
    id: str
    username: str
    bio: str | None = None

    def rename(self, username: str) -> None:
        validate_username(username)
        self.username = username
