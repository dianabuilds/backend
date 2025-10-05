from __future__ import annotations

import json
import logging
import math
from datetime import UTC, datetime, timedelta
from json import JSONDecodeError
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_role_db,
)
from domains.product.navigation.application.ports import TransitionRequest
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)
ALGO_ALIASES = {
    "fts": "embedding",
    "semantic": "embedding",
    "embedding": "embedding",
    "vector": "embedding",
    "tags": "tags",
    "tag": "tags",
    "random": "random",
    "mix": "explore",
    "explore": "explore",
    "discover": "explore",
}
ALGO_SOURCES = {
    "tags": ["tags"],
    "random": ["random"],
    "embedding": ["embedding", "fts", "semantic", "vector"],
    "explore": ["explore", "mix", "discover"],
}


DEV_BLOG_TAG = "dev-blog"


def _iso(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        return _iso(datetime.fromisoformat(str(dt)))
    except (ValueError, TypeError):
        return None


def _normalize_algo_key(algo: str | None) -> str:
    key = (algo or "").strip().lower()
    return ALGO_ALIASES.get(key, key or "tags")


def _algo_sources(key: str) -> list[str]:
    normalized = _normalize_algo_key(key)
    return ALGO_SOURCES.get(normalized, [normalized])


async def _strategy_rows(engine: AsyncEngine) -> list[dict[str, Any]]:
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
        logger.exception("navigation relations: failed to load strategy config")
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
                "strategy": _normalize_algo_key(row.get("strategy")),
                "weight": float(row.get("weight") or 0.0),
                "enabled": bool(row.get("enabled")),
                "updated_at": _iso(row.get("updated_at")),
                "meta": meta or {},
            }
        )
    # Deduplicate by normalized key keeping first occurrence
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in result:
        if item["strategy"] in seen:
            continue
        seen.add(item["strategy"])
        unique.append(item)
    return unique


async def _usage_rows(engine: AsyncEngine) -> dict[str, dict[str, Any]]:
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
        logger.exception("navigation relations: failed to load usage stats")
        return {}
    usage: dict[str, dict[str, Any]] = {}
    for row in rows:
        norm = _normalize_algo_key(row.get("algo"))
        bucket = usage.setdefault(norm, {"links": 0, "score": 0.0, "raw": {}})
        links = int(row.get("links") or 0)
        bucket["links"] += links
        bucket["score"] += float(row.get("total_score") or 0.0)
        bucket.setdefault("raw", {})[str(row.get("algo"))] = links
    return usage


async def _fetch_top_relations(
    engine: AsyncEngine, key: str, limit: int = 10
) -> list[dict[str, Any]]:
    sources = _algo_sources(key)
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
        logger.exception(
            "navigation relations: failed to load top relations for %s", key
        )
        return []
    return [
        {
            "source_id": int(row.get("source_id")),
            "source_title": row.get("source_title"),
            "source_slug": row.get("source_slug"),
            "target_id": int(row.get("target_id")),
            "target_title": row.get("target_title"),
            "target_slug": row.get("target_slug"),
            "algo": row.get("algo"),
            "score": float(row.get("score") or 0.0),
            "updated_at": _iso(row.get("updated_at")),
        }
        for row in rows
    ]


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/navigation")
    admin_required = require_role_db("moderator")

    async def _ensure_engine(container) -> AsyncEngine | None:
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if not dsn:
                return None
            if "?" in dsn:
                dsn = dsn.split("?", 1)[0]
            return get_async_engine("navigation-api", url=dsn, future=True)
        except (ValidationError, ValueError, TypeError) as exc:
            logger.warning(
                "navigation relations: invalid database configuration: %s", exc
            )
            return None
        except SQLAlchemyError:
            logger.exception("navigation relations: failed to create engine")
            return None

    @router.post("/next")
    def next_step(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "")
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        session_id = str(
            body.get("session_id")
            or req.headers.get("x-session-id")
            or req.cookies.get("session_id")
            or ""
        )
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id_required")
        origin_node_id_raw = body.get("origin_node_id")
        try:
            origin_node_id = (
                int(origin_node_id_raw) if origin_node_id_raw is not None else None
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400, detail="invalid_origin_node_id"
            ) from exc
        route_raw = body.get("route_window") or []
        if not isinstance(route_raw, (list, tuple)):
            raise HTTPException(status_code=400, detail="invalid_route_window")
        try:
            route_window = [int(x) for x in route_raw if x is not None]
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="invalid_route_window") from exc
        requested_slots_raw = body.get("ui_slots")
        try:
            requested_slots = (
                int(requested_slots_raw) if requested_slots_raw is not None else 0
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="invalid_ui_slots") from exc
        provider_overrides_raw = body.get("requested_provider_overrides") or []
        if not isinstance(provider_overrides_raw, (list, tuple)):
            provider_overrides_raw = []
        provider_overrides = [
            str(item) for item in provider_overrides_raw if isinstance(item, str)
        ]
        limit_state = str(body.get("limit_state") or "normal")
        mode = str(body.get("mode") or "normal")
        premium_level = str(
            body.get("premium_level") or claims.get("premium_level") or "free"
        )
        policies_hash = body.get("policies_hash")
        emergency = bool(body.get("emergency"))

        transition = TransitionRequest(
            user_id=uid,
            session_id=session_id,
            origin_node_id=origin_node_id,
            route_window=route_window,
            limit_state=limit_state,
            mode=mode,
            requested_ui_slots=requested_slots,
            premium_level=premium_level,
            policies_hash=str(policies_hash) if policies_hash is not None else None,
            requested_provider_overrides=provider_overrides,
            emergency=emergency,
        )

        svc = container.navigation_service
        decision = svc.next(transition)

        def _candidate_payload(item):
            return {
                "id": item.node_id,
                "badge": item.badge,
                "score": round(item.score, 4),
                "probability": round(item.probability, 4),
                "reason": {
                    key: round(float(value), 4) for key, value in item.factors.items()
                },
                "explain": item.explain,
                "provider": item.provider,
            }

        requested_echo = (
            requested_slots
            if requested_slots > 0
            else decision.context.requested_ui_slots
        )
        response = {
            "query_id": f"q-{decision.context.cache_seed[:12]}",
            "ui_slots_requested": requested_echo,
            "ui_slots": decision.ui_slots_granted,
            "limit_state": decision.limit_state,
            "mode": decision.mode,
            "emergency_used": decision.emergency_used,
            "decision": {
                "candidates": [
                    _candidate_payload(item) for item in decision.candidates
                ],
                "curated_blocked_reason": decision.curated_blocked_reason,
                "empty_pool": decision.empty_pool,
                "empty_pool_reason": decision.empty_pool_reason,
                "served_from_cache": decision.served_from_cache,
            },
            "pool_size": decision.pool_size,
            "cache_seed": decision.context.cache_seed,
            "t": decision.temperature,
            "epsilon": decision.epsilon,
            "mode_applied": decision.mode,
            "telemetry": dict(decision.telemetry),
        }
        if decision.empty_pool:
            response["fallback_suggestions"] = [
                "open_search",
                "open_map",
                "resume_trail",
            ]
        return response

    @router.get("/related/{node_id}")
    async def related_nodes(
        node_id: int,
        limit: int = Query(ge=1, le=50, default=6),
        algo: str = Query(default="tags"),
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        # Ensure DB engine
        eng = await _ensure_engine(container)
        if eng is None:
            return []
        # Load minimal current node info and decide visibility
        async with eng.connect() as _conn:
            cur = (
                (
                    await _conn.execute(
                        text(
                            "SELECT author_id::text AS author_id, is_public,"
                            "       EXISTS (SELECT 1 FROM product_node_tags WHERE node_id = :id AND slug = :dev_tag) AS is_dev_blog"
                            " FROM nodes WHERE id = :id"
                        ),
                        {"id": int(node_id), "dev_tag": DEV_BLOG_TAG},
                    )
                )
                .mappings()
                .first()
            )
            if _conn.in_transaction():
                await _conn.rollback()
        if not cur:
            raise HTTPException(status_code=404, detail="not_found")
        if bool(cur.get("is_dev_blog")):
            return []
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        allow_private = bool(
            uid and (uid == str(cur.get("author_id") or "") or role == "admin")
        )
        algo = (algo or "tags").lower()

        async def _load_tags(conn, lim: int) -> list[dict]:
            sql = text(
                """
                WITH cur_tags AS (
                  SELECT slug FROM product_node_tags WHERE node_id = :nid AND slug <> :dev_tag
                )
                SELECT n.id,
                       n.slug,
                       n.title,
                       n.cover_url,
                       n.is_public,
                       COUNT(*)::float AS score
                FROM product_node_tags t
                JOIN cur_tags ct ON ct.slug = t.slug
                JOIN nodes n ON n.id = t.node_id
                WHERE t.node_id <> :nid
                  AND (:allow OR n.is_public = true)
                  AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                GROUP BY n.id, n.slug, n.title, n.cover_url, n.is_public
                ORDER BY score DESC, n.updated_at DESC, n.id DESC
                LIMIT :lim
                """
            )
            try:
                rows = (
                    (
                        await conn.execute(
                            sql,
                            {
                                "nid": int(node_id),
                                "lim": int(lim),
                                "allow": bool(allow_private),
                                "dev_tag": DEV_BLOG_TAG,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
                return [
                    {
                        "id": int(r["id"]),
                        "slug": r.get("slug"),
                        "title": r.get("title"),
                        "cover_url": r.get("cover_url"),
                        "is_public": bool(r.get("is_public", False)),
                        "score": float(r.get("score") or 0.0),
                        "reason": "tags",
                    }
                    for r in rows
                ]
            except SQLAlchemyError:
                logger.debug(
                    "navigation related: tags query fallback triggered", exc_info=True
                )
                try:
                    if conn.in_transaction():
                        await conn.rollback()
                except SQLAlchemyError:
                    pass
                # Fallback to minimal projection for older schema using fresh connection
                sql2 = text(
                    """
                    WITH cur_tags AS (
                      SELECT slug FROM product_node_tags WHERE node_id = :nid AND slug <> :dev_tag
                    )
                    SELECT n.id,
                           n.title,
                           n.is_public,
                           COUNT(*)::float AS score
                    FROM product_node_tags t
                    JOIN cur_tags ct ON ct.slug = t.slug
                    JOIN nodes n ON n.id = t.node_id
                    WHERE t.node_id <> :nid
                      AND (:allow OR n.is_public = true)
                      AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                    GROUP BY n.id, n.title, n.is_public
                    ORDER BY score DESC, n.updated_at DESC, n.id DESC
                    LIMIT :lim
                    """
                )
                rows = (
                    (
                        await conn.execute(
                            sql2,
                            {
                                "nid": int(node_id),
                                "lim": int(lim),
                                "allow": bool(allow_private),
                                "dev_tag": DEV_BLOG_TAG,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
                return [
                    {
                        "id": int(r["id"]),
                        "slug": None,
                        "title": r.get("title"),
                        "cover_url": None,
                        "is_public": bool(r.get("is_public", False)),
                        "score": float(r.get("score") or 0.0),
                        "reason": "tags",
                    }
                    for r in rows
                ]

        async def _load_fts(conn, lim: int, query: str) -> list[dict]:
            sql = text(
                """
                SELECT n.id,
                       n.slug,
                       n.title,
                       n.cover_url,
                       n.is_public,
                       ts_rank_cd(n.search_vector, to_tsquery('simple', :query)) AS score
                FROM nodes n
                WHERE n.id <> :nid
                  AND (:allow OR n.is_public = true)
                  AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                  AND n.search_vector @@ to_tsquery('simple', :query)
                ORDER BY score DESC, n.updated_at DESC, n.id DESC
                LIMIT :lim
                """
            )
            try:
                rows = (
                    (
                        await conn.execute(
                            sql,
                            {
                                "nid": int(node_id),
                                "query": " & ".join(filter(None, query.split()[:6]))
                                or "",
                                "lim": int(lim),
                                "allow": bool(allow_private),
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
            except SQLAlchemyError:
                return []
            return [
                {
                    "id": int(r["id"]),
                    "slug": r.get("slug"),
                    "title": r.get("title"),
                    "cover_url": r.get("cover_url"),
                    "is_public": bool(r.get("is_public", False)),
                    "score": float(r.get("score") or 0.0),
                    "reason": "fts",
                }
                for r in rows
            ]

        async def _load_node_title(conn) -> str:
            row = (
                (
                    await conn.execute(
                        text(
                            "SELECT COALESCE(title,'') AS title FROM nodes WHERE id = :id"
                        ),
                        {"id": int(node_id)},
                    )
                )
                .mappings()
                .first()
            )
            return str(row.get("title") if row else "")

        # Cache helpers
        async def _get_cached(conn, algo_key: str, lim: int) -> list[dict]:
            ttl_sec = int(
                getattr(container.settings, "nav_related_ttl", 21600) or 21600
            )
            cutoff = datetime.now(UTC) - timedelta(seconds=ttl_sec)
            try:
                async with eng.begin() as c2:
                    rows = (
                        (
                            await c2.execute(
                                text(
                                    "SELECT c.target_id AS id, c.score, n.slug, n.title, n.cover_url, n.is_public \n"
                                    "FROM node_assoc_cache c JOIN nodes n ON n.id = c.target_id \n"
                                    "WHERE c.source_id = :sid AND c.algo = :algo AND c.updated_at >= :cut \n"
                                    "AND (:allow OR n.is_public = true) \n"
                                    "ORDER BY c.score DESC, n.updated_at DESC, n.id DESC LIMIT :lim"
                                ),
                                {
                                    "sid": int(node_id),
                                    "algo": algo_key,
                                    "cut": cutoff,
                                    "allow": bool(allow_private),
                                    "lim": int(lim),
                                    "dev_tag": DEV_BLOG_TAG,
                                },
                            )
                        )
                        .mappings()
                        .all()
                    )
            except SQLAlchemyError:
                return []
            return [
                {
                    "id": int(r["id"]),
                    "slug": r.get("slug"),
                    "title": r.get("title"),
                    "cover_url": r.get("cover_url"),
                    "is_public": bool(r.get("is_public", False)),
                    "score": float(r.get("score") or 0.0),
                    "reason": algo_key,
                }
                for r in rows
            ]

        async def _store_cache(conn, algo_key: str, items: list[dict]) -> None:
            if not items:
                return
            try:
                async with eng.begin() as c2:
                    for it in items:
                        await c2.execute(
                            text(
                                "INSERT INTO node_assoc_cache(source_id, target_id, algo, score, updated_at) \n"
                                "VALUES (:sid, :tid, :algo, :score, now()) \n"
                                "ON CONFLICT (source_id, target_id, algo) DO UPDATE SET score = EXCLUDED.score, updated_at = now()"
                            ),
                            {
                                "sid": int(node_id),
                                "tid": int(it["id"]),
                                "algo": algo_key,
                                "score": float(it.get("score") or 0.0),
                            },
                        )
            except SQLAlchemyError:
                # cache table may be missing; ignore storing
                return

        async with eng.connect() as conn:
            if algo in ("tags", "auto"):
                cached = await _get_cached(conn, "tags", limit)
                if cached:
                    return cached
                res = await _load_tags(conn, limit)
                await _store_cache(conn, "tags", res)
                return res
            elif algo == "fts" or algo == "embedding":
                cached = await _get_cached(conn, "fts", limit)
                if cached:
                    return cached
                title = await _load_node_title(conn)
                res = await _load_fts(conn, limit, title)
                await _store_cache(conn, "fts", res)
                return res
            elif algo == "mix" or algo == "explore":
                tags_cached = await _get_cached(conn, "tags", limit)
                fts_cached = await _get_cached(conn, "fts", limit)
                if not fts_cached:
                    title = await _load_node_title(conn)
                    fts_cached = await _load_fts(conn, limit, title)
                    await _store_cache(conn, "fts", fts_cached)
                if not tags_cached:
                    tags_cached = await _load_tags(conn, limit)
                    await _store_cache(conn, "tags", tags_cached)
                seen: set[int] = set()
                merged: list[dict] = []
                streams = [tags_cached, fts_cached]
                idx = 0
                while len(merged) < limit and any(streams):
                    cur_stream = streams[idx % 2]
                    if cur_stream:
                        item = cur_stream.pop(0)
                        if int(item["id"]) not in seen:
                            seen.add(int(item["id"]))
                            merged.append(item)
                    idx += 1
                return merged
            else:
                res = await _load_tags(conn, limit)
                await _store_cache(conn, "tags", res)
                return res

    @router.get("/relations/strategies", dependencies=[Depends(admin_required)])
    async def list_strategies(container=Depends(get_container)):
        eng = await _ensure_engine(container)
        if eng is None:
            return []
        config = await _strategy_rows(eng)
        usage = await _usage_rows(eng)
        total_links = sum(info.get("links", 0) for info in usage.values())
        for item in config:
            stats = usage.get(item["strategy"], {})
            item["links"] = int(stats.get("links", 0))
            item["score"] = float(stats.get("score", 0.0))
            item["usage_share"] = (
                float(item["links"]) / float(total_links) if total_links else 0.0
            )
        return config

    @router.patch(
        "/relations/strategies/{strategy}",
        dependencies=[Depends(admin_required), Depends(csrf_protect)],
    )
    async def update_strategy(
        strategy: str,
        payload: dict[str, Any],
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=503, detail="storage_unavailable")
        norm = _normalize_algo_key(strategy)
        weight_val: float | None = None
        weight_raw = payload.get("weight")
        if weight_raw is not None:
            try:
                weight_val = float(cast(float | int | str, weight_raw))
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="invalid_weight") from exc
            if weight_val < 0:
                raise HTTPException(
                    status_code=400, detail="weight_must_be_non_negative"
                )
        enabled_val = None
        if payload.get("enabled") is not None:
            enabled_val = bool(payload.get("enabled"))
        meta_val = payload.get("meta")
        meta_json = None
        if meta_val is not None:
            try:
                meta_json = json.dumps(meta_val)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="invalid_meta") from exc
        try:
            async with eng.begin() as conn:
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
                                "strategy": norm,
                                "weight": weight_val,
                                "enabled": enabled_val,
                                "meta": meta_json,
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
        except SQLAlchemyError as exc:
            logger.exception("navigation relations: failed to update strategy %s", norm)
            raise HTTPException(status_code=500, detail="update_failed") from exc
        if not row:
            raise HTTPException(status_code=404, detail="strategy_not_found")
        usage = await _usage_rows(eng)
        total_links = sum(info.get("links", 0) for info in usage.values())
        stats = usage.get(norm, {})
        return {
            "strategy": norm,
            "weight": float(row.get("weight") or 0.0),
            "enabled": bool(row.get("enabled")),
            "updated_at": _iso(row.get("updated_at")),
            "meta": row.get("meta") or {},
            "links": int(stats.get("links", 0)),
            "usage_share": (
                float(stats.get("links", 0)) / float(total_links)
                if total_links
                else 0.0
            ),
        }

    @router.get("/relations/overview", dependencies=[Depends(admin_required)])
    async def relations_overview(container=Depends(get_container)):
        eng = await _ensure_engine(container)
        if eng is None:
            return {"strategies": [], "popular": {}, "diversity": {}}
        config = await _strategy_rows(eng)
        usage = await _usage_rows(eng)
        total_links = sum(info.get("links", 0) for info in usage.values())
        strategies_payload: list[dict[str, Any]] = []
        for item in config:
            stats = usage.get(item["strategy"], {})
            payload = {
                "key": item["strategy"],
                "weight": item["weight"],
                "enabled": item["enabled"],
                "updated_at": item["updated_at"],
                "links": int(stats.get("links", 0)),
                "usage_share": (
                    float(stats.get("links", 0)) / float(total_links)
                    if total_links
                    else 0.0
                ),
            }
            strategies_payload.append(payload)
        shares = [p["usage_share"] for p in strategies_payload if p["links"] > 0]
        coverage = (
            float(len([p for p in strategies_payload if p["links"] > 0]))
            / float(len(strategies_payload))
            if strategies_payload
            else 0.0
        )
        entropy = -sum(s * math.log(s, 2) for s in shares if s > 0.0) if shares else 0.0
        gini = 1.0 - sum(s * s for s in shares) if shares else 0.0
        keys = {item["key"] for item in strategies_payload} | set(usage.keys())
        popular: dict[str, list[dict[str, Any]]] = {}
        for key in keys:
            popular[key] = await _fetch_top_relations(eng, key, limit=5)
        return {
            "strategies": strategies_payload,
            "popular": popular,
            "diversity": {
                "coverage": coverage,
                "entropy": entropy,
                "gini": gini,
            },
        }

    @router.get("/relations/top", dependencies=[Depends(admin_required)])
    async def top_relations(
        algo: str = Query(default="tags"),
        limit: int = Query(default=10, ge=1, le=50),
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            return {"items": []}
        norm = _normalize_algo_key(algo)
        items = await _fetch_top_relations(eng, norm, limit=limit)
        return {"items": items, "strategy": norm}

    return router
