from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.api_gateway.wires import build_container
from packages.core.config import to_async_dsn


async def _ensure_engine(dsn: str) -> AsyncEngine | None:
    try:
        adsn = to_async_dsn(dsn)
        if not adsn:
            return None
        # Strip query params that asyncpg may not recognize
        if "?" in adsn:
            adsn = adsn.split("?", 1)[0]
        return create_async_engine(adsn, future=True)
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
    # Emit events outside of transaction
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


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    container = build_container()
    eng = await _ensure_engine(container.settings.database_url)
    if eng is None:
        logging.getLogger("nodes.scheduler").warning("No database engine available; exiting")
        return
    interval = int(os.getenv("NODES_SCHEDULER_INTERVAL", "30"))
    log = logging.getLogger("nodes.scheduler")
    log.info("Starting scheduler worker; interval=%ss", interval)
    while True:
        try:
            await run_once(eng, container.events.publish, container.events.publish)
        except Exception as e:
            log.error("Scheduler tick failed: %s", e)
        await asyncio.sleep(interval)


def main() -> None:  # pragma: no cover - runtime script
    asyncio.run(main_async())


if __name__ == "__main__":  # pragma: no cover
    main()
