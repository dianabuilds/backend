from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.navigation.api.support import (
    DEV_BLOG_TAG,
    algo_sources,
    coerce_int,
    isoformat,
    normalize_algo_key,
)


async def fetch_strategy_rows(engine: AsyncEngine) -> list[dict[str, Any]]:
    """Return navigation strategy configuration rows."""

    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT strategy, weight, enabled, updated_at, meta FROM navigation_strategy_config ORDER BY strategy"
                        )
                    )
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return []

    result: list[dict[str, Any]] = []
    for row in rows:
        meta = row.get("meta")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (JSONDecodeError, TypeError, ValueError):
                meta = {"raw": meta}
        result.append(
            {
                "strategy": normalize_algo_key(row.get("strategy")),
                "weight": float(row.get("weight") or 0.0),
                "enabled": bool(row.get("enabled")),
                "updated_at": isoformat(row.get("updated_at")),
                "meta": meta or {},
            }
        )
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in result:
        if item["strategy"] in seen:
            continue
        seen.add(item["strategy"])
        unique.append(item)
    return unique


async def fetch_usage_rows(engine: AsyncEngine) -> dict[str, dict[str, Any]]:
    """Aggregate usage stats for navigation strategies."""

    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT algo, COUNT(*)::bigint AS links, SUM(score) AS total_score"
                            " FROM node_assoc_cache GROUP BY algo"
                        )
                    )
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return {}

    usage: dict[str, dict[str, Any]] = {}
    for row in rows:
        norm = normalize_algo_key(row.get("algo"))
        bucket = usage.setdefault(norm, {"links": 0, "score": 0.0, "raw": {}})
        links = coerce_int(row.get("links"), default=0) or 0
        bucket["links"] += links
        bucket["score"] += float(row.get("total_score") or 0.0)
        bucket.setdefault("raw", {})[str(row.get("algo"))] = links
    return usage


async def fetch_top_relations(
    engine: AsyncEngine, key: str, *, limit: int = 10
) -> list[dict[str, Any]]:
    """Fetch top related nodes for a given strategy alias."""

    sources = algo_sources(key)
    if not sources:
        return []
    placeholders = ", ".join(f":algo{i}" for i in range(len(sources)))
    params: dict[str, Any] = {f"algo{i}": src for i, src in enumerate(sources)}
    params["lim"] = int(limit)
    params["dev_tag"] = DEV_BLOG_TAG
    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT c.source_id, c.target_id, c.algo, c.score, c.updated_at,\n"
                            "       src.title AS source_title, src.slug AS source_slug,\n"
                            "       tgt.title AS target_title, tgt.slug AS target_slug\n"
                            "FROM node_assoc_cache c\n"
                            "JOIN nodes src ON src.id = c.source_id\n"
                            "JOIN nodes tgt ON tgt.id = c.target_id\n"
                            f"WHERE c.algo IN ({placeholders})\n"
                            "  AND NOT EXISTS (SELECT 1 FROM product_node_tags dt WHERE dt.node_id = src.id AND dt.slug = :dev_tag)\n"
                            "  AND NOT EXISTS (SELECT 1 FROM product_node_tags dt WHERE dt.node_id = tgt.id AND dt.slug = :dev_tag)\n"
                            "ORDER BY c.score DESC, c.updated_at DESC\n"
                            "LIMIT :lim"
                        ),
                        params,
                    )
                )
                .mappings()
                .all()
            )
    except SQLAlchemyError:
        return []

    items: list[dict[str, Any]] = []
    for row in rows:
        source_id = coerce_int(row.get("source_id"))
        target_id = coerce_int(row.get("target_id"))
        if source_id is None or target_id is None:
            continue
        items.append(
            {
                "source_id": source_id,
                "source_title": row.get("source_title"),
                "source_slug": row.get("source_slug"),
                "target_id": target_id,
                "target_title": row.get("target_title"),
                "target_slug": row.get("target_slug"),
                "algo": normalize_algo_key(row.get("algo")),
                "score": float(row.get("score") or 0.0),
                "updated_at": isoformat(row.get("updated_at")),
            }
        )
    return items


async def update_strategy_row(
    engine: AsyncEngine,
    strategy: str,
    *,
    weight: float | None,
    enabled: bool | None,
    meta_json: str | None,
) -> dict[str, Any] | None:
    """Update navigation strategy configuration row."""

    try:
        async with engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            "UPDATE navigation_strategy_config\n"
                            "   SET weight = COALESCE(:weight, weight),\n"
                            "       enabled = COALESCE(:enabled, enabled),\n"
                            "       meta = CASE WHEN :meta IS NULL THEN meta ELSE CAST(:meta AS jsonb) END,\n"
                            "       updated_at = now()\n"
                            " WHERE strategy = :strategy\n"
                            " RETURNING strategy, weight, enabled, updated_at, meta"
                        ),
                        {
                            "strategy": strategy,
                            "weight": weight,
                            "enabled": enabled,
                            "meta": meta_json,
                        },
                    )
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None
    except SQLAlchemyError:
        return None
