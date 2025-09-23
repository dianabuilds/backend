from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class NodesPort(Protocol):
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[dict]: ...

    def get(self, node_id: int) -> dict | None: ...
    def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> Sequence[dict]: ...


@dataclass(frozen=True)
class TransitionRequest:
    user_id: str
    session_id: str
    origin_node_id: int | None
    route_window: Sequence[int] = field(default_factory=tuple)
    limit_state: str = "normal"
    mode: str = "normal"
    requested_ui_slots: int = 3
    premium_level: str = "free"
    policies_hash: str | None = None
    tenant_id: str = "default"
    requested_provider_overrides: Sequence[str] | None = None
    emergency: bool = False
