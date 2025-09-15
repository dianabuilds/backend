from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TagView:
    slug: str
    name: str
    count: int = 0
