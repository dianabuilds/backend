"""Seed required shared blocks (header, footer) into the database.

Usage:
    python scripts/seed_shared_blocks.py [--dsn <url>] [--dry-run]

* Inserts shared blocks only if they are missing.
* Uses template defaults from `site_block_templates`.
"""

from __future__ import annotations

import argparse
import os
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


DEFAULT_ACTOR = "seed:shared-blocks"
TARGET_TEMPLATES = [
    {"template_key": "header", "block_key": "header-default"},
    {"template_key": "footer", "block_key": "footer-default"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed required shared blocks (header/footer)."
    )
    parser.add_argument(
        "--dsn",
        help="SQLAlchemy connection string. Defaults to APP_DATABASE_URL/DATABASE_URL from .env.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without modifying the database.",
    )
    return parser.parse_args()


def resolve_dsn(args: argparse.Namespace) -> str:
    if args.dsn:
        return args.dsn
    if load_dotenv:
        load_dotenv(".env")
    dsn = os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit(
            "Database DSN not provided. Use --dsn or define APP_DATABASE_URL/DATABASE_URL in environment/.env."
        )
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return dsn


def _prepare_meta(template_row: sa.Row[Any]) -> dict[str, Any]:
    meta = dict(template_row["default_meta"] or {})
    owners = template_row["owners"] or []
    if owners:
        meta.setdefault("owners", owners)
    meta.setdefault("documentation_url", template_row["documentation_url"])
    meta["seed"] = True
    meta.setdefault("template_key", template_row["key"])
    return meta


def _prepare_payload(template_row: sa.Row[Any], block_key: str) -> dict[str, Any]:
    available_locales = template_row["available_locales"] or [
        template_row["default_locale"]
    ]
    return {
        "id": uuid.uuid4(),
        "key": block_key,
        "title": template_row["title"],
        "template_id": template_row["id"],
        "scope": "shared",
        "section": template_row["section"],
        "status": "draft",
        "review_status": "none",
        "default_locale": template_row["default_locale"],
        "available_locales": available_locales,
        "data": template_row["default_data"] or {},
        "meta": _prepare_meta(template_row),
        "requires_publisher": template_row["requires_publisher"],
        "comment": "Seeded via scripts/seed_shared_blocks.py",
        "draft_version": 1,
        "updated_by": DEFAULT_ACTOR,
    }


def seed_blocks(engine: Engine, *, dry_run: bool) -> None:
    metadata = sa.MetaData()
    templates_table = sa.Table("site_block_templates", metadata, autoload_with=engine)
    blocks_table = sa.Table("site_blocks", metadata, autoload_with=engine)

    with engine.begin() as conn:
        for target in TARGET_TEMPLATES:
            template_key = target["template_key"]
            block_key = target["block_key"]

            template_row = conn.execute(
                sa.select(templates_table).where(templates_table.c.key == template_key)
            ).fetchone()
            if template_row is None:
                raise SystemExit(
                    f"Template '{template_key}' not found. Run sync script first."
                )

            existing = conn.execute(
                sa.select(blocks_table.c.id).where(blocks_table.c.key == block_key)
            ).fetchone()
            if existing:
                print(f"[skip] Block '{block_key}' already exists.")
                continue

            payload = _prepare_payload(template_row, block_key)
            if dry_run:
                print(
                    f"[dry-run] would insert block '{block_key}' with payload: {payload}"
                )
            else:
                conn.execute(blocks_table.insert().values(**payload))
                print(f"[ok] Inserted block '{block_key}'.")


def main() -> None:
    args = parse_args()
    dsn = resolve_dsn(args)
    engine = sa.create_engine(dsn)
    try:
        seed_blocks(engine, dry_run=args.dry_run)
    except SQLAlchemyError as exc:  # pragma: no cover - CLI handling
        raise SystemExit(f"Failed to seed shared blocks: {exc}") from exc


if __name__ == "__main__":  # pragma: no cover
    main()
