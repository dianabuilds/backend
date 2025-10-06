from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class ModerationSnapshotStore(Protocol):
    """Minimal interface for persistence backends used by moderation service."""

    def enabled(self) -> bool:
        return True

    async def load(self) -> dict[str, Any]:
        """Load persisted snapshot data."""

    async def save(self, payload: Mapping[str, Any]) -> None:
        """Persist the provided snapshot payload."""


__all__ = ["ModerationSnapshotStore"]
