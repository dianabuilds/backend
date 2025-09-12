from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID


Scope = Literal["navigation", "compass", "both"]


@dataclass(frozen=True)
class NavCacheInvalidated:
    """Event payload model for navigation cache invalidations.

    This represents a user or global navigation/compass cache invalidation.
    It is intended for external integrations/analytics via the Outbox.
    """

    scope: Scope
    reason: str
    user_id: UUID | None = None
    node_id: int | None = None
    slug: str | None = None


__all__ = ["NavCacheInvalidated", "Scope"]
