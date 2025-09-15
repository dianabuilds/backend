from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NextStep:
    node_id: int | None
    reason: str | None = None
