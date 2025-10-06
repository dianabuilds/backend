from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from domains.platform.notifications.application.audience_resolver import (
    AudienceResolutionError,
)
from domains.platform.notifications.domain.broadcast import (
    BroadcastAudience,
    BroadcastAudienceType,
)


class InMemoryAudienceResolver:
    """Resolve audiences using an in-memory roster instead of a database."""

    def __init__(self, *, known_users: Iterable[str] | None = None) -> None:
        seen: set[str] = set()
        roster: list[str] = []
        if known_users:
            for raw in known_users:
                identifier = str(raw or "").strip()
                if identifier and identifier not in seen:
                    seen.add(identifier)
                    roster.append(identifier)
        self._users: tuple[str, ...] = tuple(roster)

    async def iter_user_ids(
        self,
        audience: BroadcastAudience,
        *,
        batch_size: int | None = None,
    ) -> AsyncIterator[list[str]]:
        size = max(1, int(batch_size or 500))
        if audience.type is BroadcastAudienceType.ALL_USERS:
            async for chunk in self._emit_chunks(self._users, size):
                yield chunk
            return
        if audience.type is BroadcastAudienceType.EXPLICIT_USERS:
            user_ids = tuple(
                str(uid or "").strip() for uid in (audience.user_ids or ())
            )
            async for chunk in self._emit_chunks(user_ids, size):
                yield chunk
            return
        raise AudienceResolutionError(
            f"unsupported audience type in memory resolver: {audience.type}"
        )

    async def _emit_chunks(
        self, values: Iterable[str], size: int
    ) -> AsyncIterator[list[str]]:
        bucket: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            bucket.append(value)
            if len(bucket) >= size:
                yield bucket.copy()
                bucket.clear()
        if bucket:
            yield bucket.copy()


__all__ = ["InMemoryAudienceResolver"]
