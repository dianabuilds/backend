from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

from . import get_worker_container


async def _ensure_engine(dsn: str) -> AsyncEngine | None:
    try:
        adsn = to_async_dsn(dsn)
        if not adsn:
            return None
        return get_async_engine("nodes-scheduler", url=adsn, future=True)
    except Exception:
        return None


async def _tick_publish(conn) -> list[dict]:
    sql = text(
        """
        UPDATE nodes AS n
        SET status = 'published', is_public = true, updated_at = now()
        WHERE n.status = 'scheduled'
          AND n.publish_at IS NOT NULL
          AND n.publish_at <= now()
        RETURNING n.id, n.slug, n.author_id::text AS author_id, n.title
        """
    )
    rows = (await conn.execute(sql)).mappings().all()
    return [dict(r) for r in rows]


async def _tick_unpublish(conn) -> list[dict]:
    sql = text(
        """
        UPDATE nodes AS n
        SET status = 'archived', is_public = false, updated_at = now()
        WHERE n.status = 'scheduled_unpublish'
          AND n.unpublish_at IS NOT NULL
          AND n.unpublish_at <= now()
        RETURNING n.id, n.slug, n.author_id::text AS author_id, n.title
        """
    )
    rows = (await conn.execute(sql)).mappings().all()
    return [dict(r) for r in rows]


async def run_once(engine: AsyncEngine, publish_cb, unpublish_cb) -> None:
    async with engine.begin() as conn:
        posted = await _tick_publish(conn)
        unposted = await _tick_unpublish(conn)
    now_iso = datetime.now(UTC).isoformat()
    for r in posted:
        try:
            publish_cb(
                "node.posted.v1",
                {
                    "id": r["id"],
                    "slug": r.get("slug"),
                    "author_id": r.get("author_id"),
                    "posted_at": now_iso,
                },
                key=f"node:{r['id']}",
            )
        except Exception:
            pass
    for r in unposted:
        try:
            unpublish_cb(
                "node.unposted.v1",
                {
                    "id": r["id"],
                    "slug": r.get("slug"),
                    "author_id": r.get("author_id"),
                    "unposted_at": now_iso,
                },
                key=f"node:{r['id']}",
            )
        except Exception:
            pass


async def _main_async(interval: int | None) -> None:
    logger = logging.getLogger("nodes.scheduler")
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    container = get_worker_container()
    engine = await _ensure_engine(str(container.settings.database_url))
    if engine is None:
        logger.warning("No database engine available; exiting")
        return

    tick_interval = interval or int(os.getenv("NODES_SCHEDULER_INTERVAL", "30"))
    logger.info("Starting scheduler worker; interval=%ss", tick_interval)
    while True:
        try:
            await run_once(engine, container.events.publish, container.events.publish)
        except Exception as exc:  # pragma: no cover - log for observability
            logger.error("Scheduler tick failed: %s", exc)
        await asyncio.sleep(tick_interval)


def run(*, interval: int | None = None) -> None:
    asyncio.run(_main_async(interval))


def main() -> None:  # pragma: no cover - runtime script
    run()


if __name__ == "__main__":  # pragma: no cover
    main()
