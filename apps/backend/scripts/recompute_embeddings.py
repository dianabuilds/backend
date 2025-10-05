from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api_gateway.wires import build_container

logger = logging.getLogger(__name__)
from domains.product.nodes.application.service import NodeService
from packages.core.config import Settings, load_settings, to_async_dsn


async def _fetch_node_ids(engine) -> list[int]:
    async with engine.begin() as conn:
        rows = await conn.execute(
            text(
                "SELECT id FROM nodes WHERE status IS DISTINCT FROM 'deleted' ORDER BY id"
            )
        )
        return [int(r[0]) for r in rows]


async def _recompute_for_ids(
    service: NodeService, node_ids: Iterable[int]
) -> tuple[int, int, int]:
    updated = 0
    skipped = 0
    failed = 0
    for node_id in node_ids:
        view = service.get(node_id)
        if view is None:
            skipped += 1
            continue
        embedding_vec = await service._compute_embedding_vector(  # type: ignore[attr-defined]
            title=view.title,
            tags=view.tags,
            content_html=view.content_html,
        )
        if embedding_vec is None:
            skipped += 1
            continue
        try:
            await service.repo.update(view.id, embedding=embedding_vec)
            updated += 1
        except Exception as exc:  # pragma: no cover - defensive
            failed += 1
            logger.warning(
                "embedding_recompute_update_failed",
                extra={"node_id": view.id},
                exc_info=exc,
            )
    return updated, skipped, failed


async def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    parser = argparse.ArgumentParser(description="Recompute node embeddings")
    parser.add_argument(
        "--limit", type=int, default=None, help="Process only the first N nodes"
    )
    args = parser.parse_args(argv)

    settings: Settings = load_settings()
    container = build_container(env=settings.env)
    service = container.nodes_service

    dsn = to_async_dsn(settings.database_url)
    if not dsn:
        raise RuntimeError("database_url is not configured")
    engine = create_async_engine(dsn)

    node_ids = await _fetch_node_ids(engine)
    if args.limit is not None:
        node_ids = node_ids[: args.limit]

    updated, skipped, failed = await _recompute_for_ids(service, node_ids)
    total = len(node_ids)
    logger.info(
        "embedding_recompute_summary total=%s updated=%s skipped=%s failed=%s",
        total,
        updated,
        skipped,
        failed,
    )


if __name__ == "__main__":
    asyncio.run(main())
