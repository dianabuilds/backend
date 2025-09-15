from __future__ import annotations

"""
Backfill script template: migrate data from legacy DB to new DDD schema.

Usage examples:
  APP_DATABASE_URL=postgresql://app:app@localhost:5432/app \
  python apps/backendDDD/infra/dev/backfill_legacy_to_new.py --from-csv ./export

Or provide a legacy DSN (implement readers accordingly):
  LEGACY_DSN=postgresql://legacy:pass@host:5432/legacy \
  APP_DATABASE_URL=postgresql://app:app@localhost:5432/app \
  python apps/backendDDD/infra/dev/backfill_legacy_to_new.py --from-db

Notes:
- This is a scaffold. Replace read_* impls with real legacy readers.
- The script is idempotent: uses upserts and ON CONFLICT where possible.
"""

import argparse
import os
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


@dataclass
class NodeRow:
    id: int
    author_id: str
    title: str | None
    is_public: bool
    tags: list[str]


async def _write_nodes(engine: AsyncEngine, rows: Iterable[NodeRow]) -> int:
    n = 0
    async with engine.begin() as conn:
        for r in rows:
            await conn.execute(
                text(
                    """
                    INSERT INTO product_nodes(id, author_id, title, is_public)
                    VALUES (:id, cast(:aid as uuid), :title, :pub)
                    ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, is_public = EXCLUDED.is_public, updated_at = now()
                    """
                ),
                {"id": int(r.id), "aid": r.author_id, "title": r.title, "pub": bool(r.is_public)},
            )
            await conn.execute(text("DELETE FROM product_node_tags WHERE node_id = :id"), {"id": int(r.id)})
            for t in sorted(set(s.strip().lower() for s in (r.tags or []) if s)):
                await conn.execute(
                    text(
                        "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                    ),
                    {"id": int(r.id), "slug": t},
                )
            n += 1
    return n


def read_nodes_from_csv(path: str) -> list[NodeRow]:
    # Placeholder: implement CSV parser that yields NodeRow
    # Expect files: nodes.csv, node_tags.csv
    return []


async def main() -> None:
    parser = argparse.ArgumentParser(description="Legacy -> DDD backfill (template)")
    parser.add_argument("--from-csv", type=str, default=None, help="Path to CSV export folder")
    parser.add_argument("--from-db", action="store_true", help="Read from legacy DB (implement)")
    args = parser.parse_args()

    dsn = os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("Set APP_DATABASE_URL")
    engine = create_async_engine(dsn)

    if args.from_csv:
        nodes = read_nodes_from_csv(args.from_csv)
        count = await _write_nodes(engine, nodes)
        print(f"Backfilled nodes: {count}")
    elif args.from_db:
        # Implement legacy readers here using create_async_engine(LEGACY_DSN)
        print("--from-db not implemented: provide legacy readers")
    else:
        print("Specify --from-csv or --from-db")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

