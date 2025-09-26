from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.events.service import Events
from packages.core.db import get_async_engine


class SQLTagUsageWriter:
    """Event-driven writer for tag_usage_counters.

    Handles topics like `node.tags.updated.v1` with payload shape:
      {
        "author_id": "<uuid>",
        "content_type": "node",
        "added": ["tag-a", ...],
        "removed": ["tag-b", ...]
      }
    """

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("tags-usage", url=engine) if isinstance(engine, str) else engine
        )

    async def apply(self, payload: dict[str, Any]) -> None:
        aid = str(payload.get("author_id") or "").strip()
        if not aid:
            return
        ctype = str(payload.get("content_type") or "node").strip() or "node"
        added = [str(s).strip().lower() for s in (payload.get("added") or []) if str(s).strip()]
        removed = [str(s).strip().lower() for s in (payload.get("removed") or []) if str(s).strip()]
        if not added and not removed:
            return
        async with self._engine.begin() as conn:
            # Upsert increments for added
            if added:
                sql_inc = text(
                    """
                    INSERT INTO tag_usage_counters(author_id, content_type, slug, count)
                    VALUES (cast(:aid as uuid), :ctype, :slug, 1)
                    ON CONFLICT (author_id, content_type, slug)
                    DO UPDATE SET count = tag_usage_counters.count + 1
                    """
                )
                for s in added:
                    await conn.execute(sql_inc, {"aid": aid, "ctype": ctype, "slug": s})
            # Decrements for removed (and cleanup if zero)
            if removed:
                sql_dec = text(
                    """
                    UPDATE tag_usage_counters
                    SET count = GREATEST(count - 1, 0)
                    WHERE author_id = cast(:aid as uuid) AND content_type = :ctype AND slug = :slug
                    """
                )
                sql_del = text(
                    """
                    DELETE FROM tag_usage_counters
                    WHERE author_id = cast(:aid as uuid) AND content_type = :ctype AND slug = :slug AND count <= 0
                    """
                )
                for s in removed:
                    await conn.execute(sql_dec, {"aid": aid, "ctype": ctype, "slug": s})
                    await conn.execute(sql_del, {"aid": aid, "ctype": ctype, "slug": s})


def register_tags_usage_writer(events: Events, engine_or_dsn: AsyncEngine | str) -> None:
    """Register event consumers for tags usage counters.

    Safe to call without DB: failures are swallowed to avoid breaking API startup.
    """
    try:
        writer = SQLTagUsageWriter(engine_or_dsn)

        async def _on_node_tags_updated(_topic: str, payload: dict[str, Any]) -> None:
            try:
                await writer.apply(payload)
            except Exception:
                # best-effort: do not crash relay
                pass

        loop = asyncio.get_running_loop()
        events.on(
            "node.tags.updated.v1",
            lambda t, p: loop.create_task(_on_node_tags_updated(t, p)),
        )
        # Optionally, support quest tags event name if present in the system
        events.on(
            "quest.tags.updated.v1",
            lambda t, p: loop.create_task(_on_node_tags_updated(t, p)),
        )
    except Exception:
        # No DB / engine issues — skip registration silently
        return


__all__ = ["SQLTagUsageWriter", "register_tags_usage_writer"]
