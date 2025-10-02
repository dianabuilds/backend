from __future__ import annotations

import asyncio
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.db import get_async_engine


class SQLUsageProjection:
    """Persist tag usage counters directly in Postgres."""

    def __init__(self, engine: AsyncEngine | str, *, content_type: str = "node") -> None:
        self._engine: AsyncEngine = (
            engine if isinstance(engine, AsyncEngine) else get_async_engine("tags", url=engine)
        )
        self._content_type = content_type

    def apply_diff(self, author_id: str, added: Sequence[str], removed: Sequence[str]) -> None:
        aid = (author_id or "").strip()
        added_slugs = [str(s).strip().lower() for s in added if str(s).strip()]
        removed_slugs = [str(s).strip().lower() for s in removed if str(s).strip()]
        if not aid or (not added_slugs and not removed_slugs):
            return

        async def _run() -> None:
            async with self._engine.begin() as conn:
                if added_slugs:
                    sql_inc = text(
                        """
                        INSERT INTO tag_usage_counters(author_id, content_type, slug, count)
                        VALUES (cast(:aid as uuid), :ctype, :slug, 1)
                        ON CONFLICT (author_id, content_type, slug)
                        DO UPDATE SET count = tag_usage_counters.count + 1
                        """
                    )
                    for slug in added_slugs:
                        await conn.execute(
                            sql_inc,
                            {"aid": aid, "ctype": self._content_type, "slug": slug},
                        )
                if removed_slugs:
                    sql_dec = text(
                        """
                        UPDATE tag_usage_counters
                           SET count = GREATEST(count - 1, 0)
                         WHERE author_id = cast(:aid as uuid)
                           AND content_type = :ctype
                           AND slug = :slug
                        """
                    )
                    sql_del = text(
                        """
                        DELETE FROM tag_usage_counters
                         WHERE author_id = cast(:aid as uuid)
                           AND content_type = :ctype
                           AND slug = :slug
                           AND count <= 0
                        """
                    )
                    for slug in removed_slugs:
                        await conn.execute(
                            sql_dec,
                            {"aid": aid, "ctype": self._content_type, "slug": slug},
                        )
                        await conn.execute(
                            sql_del,
                            {"aid": aid, "ctype": self._content_type, "slug": slug},
                        )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.create_task(_run())


__all__ = ["SQLUsageProjection"]
