from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Flag:
    slug: str
    enabled: bool = True
    description: str | None = None
    rollout: int = 100  # 0..100
    users: set[str] = field(default_factory=set)
    roles: set[str] = field(default_factory=set)
    meta: dict[str, Any] | None = None


__all__ = ["Flag"]
