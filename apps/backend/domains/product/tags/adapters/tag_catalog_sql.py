from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from threading import Lock

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.db import get_async_engine

log = logging.getLogger(__name__)


class SQLTagCatalog:
    """Canonical tag helper backed by Postgres data (tags, aliases, blacklist).

    Data is cached in-memory with a short TTL and refreshed asynchronously
    whenever it becomes stale. This keeps the synchronous TagCatalog port
    compatible with async database access.
    """

    def __init__(
        self,
        engine: AsyncEngine | str,
        *,
        cache_ttl: float = 30.0,
    ) -> None:
        self._engine: AsyncEngine = (
            engine if isinstance(engine, AsyncEngine) else get_async_engine("tags", url=engine)
        )
        self._cache_ttl = max(float(cache_ttl), 0.0)
        self._lock = Lock()
        self._aliases: dict[str, str] = {}
        self._blacklist: set[str] = set()
        self._loaded_at: float = 0.0
        self._refreshing: bool = False
        self._schedule_refresh()

    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]:
        """Normalise, apply aliases, enforce blacklist, and remove duplicates."""
        self._maybe_schedule_refresh()
        seen: set[str] = set()
        result: list[str] = []
        aliases = self._aliases
        blacklist = self._blacklist
        for item in slugs:
            slug = (item or "").strip().lower()
            if not slug:
                continue
            canonical = aliases.get(slug, slug)
            if canonical in blacklist:
                raise ValueError(f"blacklisted: {canonical}")
            if canonical not in seen:
                seen.add(canonical)
                result.append(canonical)
        return result

    def _maybe_schedule_refresh(self) -> None:
        if self._cache_ttl <= 0:
            return
        now = time.monotonic()
        if now - self._loaded_at < self._cache_ttl:
            return
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        with self._lock:
            if self._refreshing:
                return
            self._refreshing = True

        async def runner() -> None:
            try:
                await self._refresh()
            except Exception as exc:  # pragma: no cover - defensive logging
                log.exception("tag_catalog_refresh_failed", exc_info=exc)
            finally:
                with self._lock:
                    self._refreshing = False

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(runner())
            except Exception:
                # already logged inside runner
                pass
        else:
            task = loop.create_task(runner())
            task.add_done_callback(lambda t: t.exception())

    async def _refresh(self) -> None:
        aliases: dict[str, str] = {}
        blacklist: set[str] = set()
        sql_aliases = text(
            """
            SELECT LOWER(a.alias) AS alias, LOWER(t.slug) AS slug
              FROM tag_alias AS a
              JOIN tag AS t ON t.id = a.tag_id
            """
        )
        sql_blacklist = text("SELECT LOWER(slug) AS slug FROM tag_blacklist")
        async with self._engine.begin() as conn:
            alias_rows = (await conn.execute(sql_aliases)).mappings().all()
            for row in alias_rows:
                alias = str(row.get("alias") or "").strip()
                target = str(row.get("slug") or "").strip()
                if alias and target:
                    aliases[alias] = target
            blacklist_rows = (await conn.execute(sql_blacklist)).mappings().all()
            for row in blacklist_rows:
                slug = str(row.get("slug") or "").strip()
                if slug:
                    blacklist.add(slug)
        with self._lock:
            self._aliases = aliases
            self._blacklist = blacklist
            self._loaded_at = time.monotonic()


__all__ = ["SQLTagCatalog"]
