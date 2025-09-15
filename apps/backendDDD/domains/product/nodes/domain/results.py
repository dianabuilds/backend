from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeView:
    id: int
    author_id: str
    title: str | None
    tags: list[str]
    is_public: bool
