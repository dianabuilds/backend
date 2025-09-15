from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class NodesPort(Protocol):
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[dict]: ...
    def get(self, node_id: int) -> dict | None: ...


@dataclass(frozen=True)
class NextInput:
    user_id: str
    current_node_id: int | None = None
    strategy: str = "random"
