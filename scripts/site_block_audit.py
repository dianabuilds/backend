from __future__ import annotations

import argparse
import os
from typing import Iterable

import sqlalchemy as sa
from sqlalchemy.engine import Engine, Row, create_engine


DEFAULT_QUERIES: tuple[tuple[str, str], ...] = (
    (
        "Blocks by scope & status",
        """
        SELECT scope, status, COUNT(*) AS count
        FROM site_blocks
        GROUP BY scope, status
        ORDER BY scope, status;
        """,
    ),
    (
        "Blocks by scope & section (top 20)",
        """
        SELECT scope, section, COUNT(*) AS count
        FROM site_blocks
        GROUP BY scope, section
        ORDER BY scope, count DESC
        LIMIT 20;
        """,
    ),
    (
        "Shared blocks without template",
        """
        SELECT id, key, title, section, status, updated_at
        FROM site_blocks
        WHERE scope = 'shared' AND template_id IS NULL
        ORDER BY updated_at DESC
        LIMIT 20;
        """,
    ),
    (
        "Block meta keys",
        """
        SELECT key, COUNT(*) AS count
        FROM (
            SELECT jsonb_object_keys(meta) AS key
            FROM site_blocks
            WHERE meta IS NOT NULL AND jsonb_typeof(meta) = 'object'
        ) AS keys
        GROUP BY key
        ORDER BY count DESC, key;
        """,
    ),
    (
        "Block extras keys",
        """
        SELECT key, COUNT(*) AS count
        FROM (
            SELECT jsonb_object_keys(extras) AS key
            FROM site_blocks
            WHERE extras IS NOT NULL AND jsonb_typeof(extras) = 'object'
        ) AS keys
        GROUP BY key
        ORDER BY count DESC, key;
        """,
    ),
    (
        "Templates by status",
        """
        SELECT status, COUNT(*) AS count
        FROM site_block_templates
        GROUP BY status
        ORDER BY status;
        """,
    ),
    (
        "Templates by section",
        """
        SELECT section, COUNT(*) AS count
        FROM site_block_templates
        GROUP BY section
        ORDER BY count DESC, section
        LIMIT 20;
        """,
    ),
    (
        "Template meta keys",
        """
        SELECT key, COUNT(*) AS count
        FROM (
            SELECT jsonb_object_keys(default_meta) AS key
            FROM site_block_templates
            WHERE default_meta IS NOT NULL AND jsonb_typeof(default_meta) = 'object'
        ) AS keys
        GROUP BY key
        ORDER BY count DESC, key;
        """,
    ),
    (
        "Blocks per template",
        """
        SELECT t.key AS template_key,
               t.title AS template_title,
               COUNT(b.id) AS block_count
        FROM site_block_templates t
        LEFT JOIN site_blocks b ON b.template_id = t.id
        GROUP BY t.id, t.key, t.title
        ORDER BY block_count DESC, template_key
        LIMIT 20;
        """,
    ),
)


def iterate_rows(engine: Engine, query: str) -> list[Row]:
    with engine.connect() as conn:
        result = conn.execute(sa.text(query))
        return list(result.fetchall())


def print_rows(title: str, rows: Iterable[Row]) -> None:
    rows = list(rows)
    print(f"\n== {title}")
    if not rows:
        print("  (no rows)")
        return
    keys = list(rows[0]._mapping.keys())
    widths = [
        max(len(str(key)), *(len(str(row._mapping[key])) for row in rows))
        for key in keys
    ]
    header = "  " + " | ".join(
        f"{key:<{width}}" for key, width in zip(keys, widths, strict=True)
    )
    print(header)
    print("  " + "-+-".join("-" * width for width in widths))
    for row in rows:
        mapping = row._mapping
        line = "  " + " | ".join(
            f"{mapping[key]!s:<{width}}"
            for key, width in zip(keys, widths, strict=True)
        )
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect site editor blocks/templates state."
    )
    parser.add_argument(
        "--dsn",
        help="Async SQLAlchemy DSN (default: $APP_DATABASE_URL or $DATABASE_URL)",
        default=os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL"),
    )
    args = parser.parse_args()

    if not args.dsn:
        raise SystemExit("Provide DSN via --dsn or APP_DATABASE_URL / DATABASE_URL.")

    engine = create_engine(args.dsn, future=True)
    for title, query in DEFAULT_QUERIES:
        try:
            rows = iterate_rows(engine, query)
        except sa.exc.SQLAlchemyError as exc:  # type: ignore[attr-defined]
            print(f"\n== {title}\n  ! query failed: {exc.__class__.__name__}: {exc}")
            continue
        print_rows(title, rows)


if __name__ == "__main__":
    main()
