from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - only for typing
    from sqlalchemy.ext.asyncio import AsyncEngine
else:  # pragma: no cover - optional SQL dependency
    try:
        from sqlalchemy.ext.asyncio import AsyncEngine  # type: ignore
    except ImportError:  # pragma: no cover
        AsyncEngine = Any  # type: ignore[misc,assignment]

from .base import ModerationSnapshotStore
from .memory import InMemoryModerationStorage
from .sql import SQLModerationStorage

__all__ = [
    "ModerationSnapshotStore",
    "InMemoryModerationStorage",
    "SQLModerationStorage",
    "create_storage",
]


def create_storage(engine: AsyncEngine | None) -> ModerationSnapshotStore:
    """Factory selecting SQL or in-memory snapshot backend."""
    if engine is None:
        return InMemoryModerationStorage()
    return SQLModerationStorage(engine)
