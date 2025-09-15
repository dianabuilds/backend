from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class QuestView:
    id: str
    author_id: str
    slug: str
    title: str
    description: str | None
    tags: Sequence[str]
    is_public: bool
