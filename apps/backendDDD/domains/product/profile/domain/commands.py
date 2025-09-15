from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateUsername:
    user_id: str
    username: str
