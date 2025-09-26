from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.domain.broadcast import (
    BroadcastAudience,
    BroadcastAudienceType,
)

from ..adapters._engine import ensure_async_engine


class AudienceResolutionError(RuntimeError):
    """Raised when a broadcast audience cannot be materialized."""


class BroadcastAudienceResolver:
    """Resolve broadcast audiences into batches of user identifiers."""

    def __init__(
        self,
        engine: AsyncEngine | str,
        *,
        default_batch_size: int = 500,
    ) -> None:
        self._engine = ensure_async_engine(engine, name="notifications-audience")
        self._default_batch_size = max(1, int(default_batch_size))

    async def iter_user_ids(
        self,
        audience: BroadcastAudience,
        *,
        batch_size: int | None = None,
    ) -> AsyncIterator[list[str]]:
        size = max(1, int(batch_size or self._default_batch_size))
        if audience.type is BroadcastAudienceType.ALL_USERS:
            async for chunk in self._iter_all_users(size):
                if chunk:
                    yield chunk
            return
        if audience.type is BroadcastAudienceType.EXPLICIT_USERS:
            async for chunk in self._iter_explicit_users(audience.user_ids or (), size):
                if chunk:
                    yield chunk
            return
        if audience.type is BroadcastAudienceType.SEGMENT:
            raise AudienceResolutionError("segment audiences are not supported yet")
        raise AudienceResolutionError(f"unsupported audience type: {audience.type}")

    async def _iter_all_users(self, batch_size: int) -> AsyncIterator[list[str]]:
        query = text(
            """
            SELECT id::text AS id
            FROM users
            WHERE is_active IS DISTINCT FROM FALSE
            ORDER BY id
            LIMIT :limit OFFSET :offset
            """
        )
        offset = 0
        async with self._engine.begin() as conn:
            while True:
                rows = (
                    (
                        await conn.execute(
                            query,
                            {"limit": batch_size, "offset": offset},
                        )
                    )
                    .scalars()
                    .all()
                )
                if not rows:
                    break
                yield [str(value) for value in rows]
                offset += len(rows)

    async def _iter_explicit_users(
        self, user_ids: Sequence[str], batch_size: int
    ) -> AsyncIterator[list[str]]:
        chunk: list[str] = []
        seen: set[str] = set()
        for raw in user_ids:
            identifier = str(raw or "").strip()
            if not identifier or identifier in seen:
                continue
            seen.add(identifier)
            chunk.append(identifier)
            if len(chunk) >= batch_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


__all__ = ["AudienceResolutionError", "BroadcastAudienceResolver"]
