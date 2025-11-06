from __future__ import annotations

import hashlib
import inspect
import logging
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend.app.api_gateway.routers import get_container
from apps.backend.infra.security.rate_limits import PUBLIC_RATE_LIMITS
from domains.product.content.application import (
    DevBlogDataService,
    HomeComposer,
    HomeConfigService,
    InMemoryHomeCache,
    NodeDataService,
    QuestDataService,
)
from domains.product.content.domain import (
    HomeConfig,
    HomeConfigRepositoryError,
    HomeConfigStatus,
)
from domains.product.content.infrastructure import RedisHomeCache
from domains.product.content.infrastructure.home_config_repository import (
    HomeConfigRepository,
)
from domains.product.nodes.application.use_cases.catalog import build_dev_blog_service
from domains.product.site.infrastructure.repositories import helpers as site_helpers
from domains.product.site.infrastructure.tables import (
    SITE_PAGE_VERSIONS_TABLE,
    SITE_PAGES_TABLE,
)
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

try:
    from prometheus_client import Histogram  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Histogram = None  # type: ignore[misc, assignment]

try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]

try:
    from redis.exceptions import RedisError  # type: ignore[import]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]

logger = logging.getLogger("domains.product.content.api.home")

if Histogram is not None:
    PUBLIC_HOME_LATENCY = Histogram(
        "public_home_latency_seconds",
        "Latency of GET /v1/public/home responses",
        buckets=(0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
else:
    PUBLIC_HOME_LATENCY = None

_DEFAULT_SLUG = "main"
_CACHE_CONTROL = "public, max-age=300"
_SQL_DATETIME_FMT = 'YYYY-MM-DD"T"HH24:MI:SS"Z"'


class PublicHomeResponse(BaseModel):
    slug: str
    version: int
    updated_at: str | None
    published_at: str | None
    generated_at: str | None
    blocks: list[dict[str, Any]]
    meta: dict[str, Any]
    fallbacks: list[dict[str, Any]]


def make_public_router() -> APIRouter:
    router = APIRouter(prefix="/v1/public", tags=["public-home"])

    content_rate_limit = PUBLIC_RATE_LIMITS["content"].as_dependencies()

    @router.get(
        "/home",
        response_model=PublicHomeResponse,
        summary="Get published home configuration",
        dependencies=content_rate_limit,
    )
    async def get_public_home(
        request: Request,
        slug: str = Query(default=_DEFAULT_SLUG, min_length=1, max_length=128),
        container=Depends(get_container),
    ) -> Response:
        composer = _get_home_composer(container)
        config = await _load_site_home_config(container, slug)
        if config is None:
            service = _get_home_config_service(container)
            try:
                config = await service.get_active(slug)
            except HomeConfigRepositoryError as exc:  # pragma: no cover - defensive
                logger.error("home.config_repository_error", exc_info=exc)
                raise HTTPException(
                    status_code=503, detail="home_storage_unavailable"
                ) from exc
        if config is None:
            raise HTTPException(status_code=404, detail="home_config_not_found")

        start_time = time.perf_counter()
        payload = await composer.compose(config)
        etag = _compute_etag(config)
        if_none_match = request.headers.get("if-none-match")
        headers = {"ETag": etag, "Cache-Control": _CACHE_CONTROL}
        if if_none_match and etag in {tag.strip() for tag in if_none_match.split(",")}:
            response: Response = Response(status_code=304, headers=headers)
        else:
            response = JSONResponse(content=payload, headers=headers)

        if PUBLIC_HOME_LATENCY is not None:
            PUBLIC_HOME_LATENCY.observe(time.perf_counter() - start_time)
        return response

    return router


def get_home_composer(container) -> HomeComposer:
    return _get_home_composer(container)


async def _load_site_home_config(container, slug: str) -> HomeConfig | None:
    normalized = slug.strip() or _DEFAULT_SLUG
    if normalized.startswith("/"):
        normalized = normalized.removeprefix("/")
    candidates: list[str] = [normalized]
    if normalized == "main":
        candidates.append("/")
    elif normalized == "":
        candidates = ["main", "/"]
    engine = await _ensure_home_engine(container)
    if engine is None:
        return None
    async with engine.connect() as conn:
        page_stmt = (
            sa.select(
                SITE_PAGES_TABLE.c.id,
                SITE_PAGES_TABLE.c.slug,
                SITE_PAGES_TABLE.c.title,
                SITE_PAGES_TABLE.c.created_at,
                SITE_PAGES_TABLE.c.updated_at,
                SITE_PAGES_TABLE.c.published_version,
                SITE_PAGES_TABLE.c.type,
            )
            .where(SITE_PAGES_TABLE.c.slug.in_(candidates))
            .limit(1)
        )
        page_row = (await conn.execute(page_stmt)).mappings().first()
        if not page_row:
            return None
        published_version = page_row.get("published_version")
        if published_version is None:
            return None
        try:
            published_version_int = int(published_version)
        except (TypeError, ValueError):
            return None
        version_stmt = (
            sa.select(
                SITE_PAGE_VERSIONS_TABLE.c.data,
                SITE_PAGE_VERSIONS_TABLE.c.meta,
                SITE_PAGE_VERSIONS_TABLE.c.published_at,
                SITE_PAGE_VERSIONS_TABLE.c.published_by,
            )
            .where(
                sa.and_(
                    SITE_PAGE_VERSIONS_TABLE.c.page_id == page_row["id"],
                    SITE_PAGE_VERSIONS_TABLE.c.version == published_version_int,
                )
            )
            .limit(1)
        )
        version_row = (await conn.execute(version_stmt)).mappings().first()
        if not version_row:
            return None
    data = site_helpers.as_mapping(version_row.get("data"))
    meta = site_helpers.as_mapping(version_row.get("meta"))
    payload = dict(data)
    if meta and not isinstance(data.get("meta"), dict):
        payload["meta"] = meta
    else:
        payload["meta"] = site_helpers.as_mapping(payload.get("meta"))
    published_at = version_row.get("published_at")
    updated_at = page_row.get("updated_at") or published_at or datetime.now(UTC)
    created_at = page_row.get("created_at") or datetime.now(UTC)
    status = HomeConfigStatus.PUBLISHED
    return HomeConfig(
        id=page_row["id"],
        slug=page_row.get("slug") or normalized or "main",
        version=published_version_int,
        status=status,
        data=payload,
        created_by=None,
        updated_by=version_row.get("published_by"),
        created_at=created_at,
        updated_at=updated_at,
        published_at=published_at,
        draft_of=None,
    )


def _compute_etag(config: HomeConfig) -> str:
    updated = _iso(config.updated_at) or ""
    base = f"{config.slug}:{config.version}:{updated}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f'"{digest}"'


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _get_home_config_service(container) -> HomeConfigService:
    cached = getattr(container, "_home_config_service", None)
    if cached is not None:
        return cached

    async def factory() -> AsyncEngine | None:
        return await _ensure_home_engine(container)

    repository = HomeConfigRepository(factory)
    service = HomeConfigService(repository=repository)
    container._home_config_service = service
    return service


def _get_home_composer(container) -> HomeComposer:
    cached = getattr(container, "_home_composer", None)
    if cached is not None:
        return cached
    settings = getattr(container, "settings", None)
    ttl_value = getattr(settings, "home_cache_ttl", 300)
    try:
        ttl = int(ttl_value)
    except (TypeError, ValueError):
        ttl = 300
    prefix = getattr(settings, "home_cache_key_prefix", "home:public")
    enabled = bool(getattr(settings, "home_cache_enabled", True))
    redis_override = (
        getattr(settings, "home_cache_redis_url", None) if settings else None
    )
    redis_url = redis_override or (
        getattr(settings, "redis_url", None) if settings else None
    )
    cache = getattr(container, "_home_cache", None)
    if cache is None:
        cache = _build_home_cache(
            container,
            ttl=ttl,
            enabled=enabled,
            redis_url=str(redis_url) if redis_url else None,
        )
        container._home_cache = cache
    node_service = _build_node_data_service(container)
    quest_service = _build_quest_data_service(container)
    dev_blog_service = _build_dev_blog_data_service(container, node_service)
    composer = HomeComposer(
        cache=cache,
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
        cache_ttl=ttl,
        cache_prefix=str(prefix or "home:public"),
    )
    container._home_composer = composer
    return composer


def _build_home_cache(container, *, ttl: int, enabled: bool, redis_url: str | None):
    if enabled and aioredis is not None and redis_url:
        try:
            client = getattr(container, "_home_cache_client", None)
            if client is None:
                client = aioredis.from_url(
                    redis_url, encoding="utf-8", decode_responses=False
                )
                container._home_cache_client = client
            return RedisHomeCache(client, default_ttl=ttl)
        except (RedisError, ValueError, TypeError) as exc:
            logger.warning(
                "home.cache.redis_init_failed",
                extra={"url": redis_url},
                exc_info=exc,
            )
    return InMemoryHomeCache(default_ttl=ttl)


def _build_node_data_service(container) -> NodeDataService:
    svc = getattr(container, "nodes_service", None)

    async def fetch_many(items: Sequence[str | int]):
        if svc is None:
            return []
        cache: dict[str, dict[str, Any]] = {}
        for item in items:
            ref = str(item)
            if ref in cache:
                continue
            card = await _fetch_node_card(svc, ref)
            if card is None:
                continue
            cache[ref] = card
            card_id = card.get("id")
            if card_id is not None:
                cache[str(card_id)] = card
            slug = card.get("slug")
            if isinstance(slug, str):
                cache[slug] = card
        ordered: list[dict[str, Any]] = []
        for item in items:
            ref = str(item)
            card = cache.get(ref)
            if card is None and ref.isdigit():
                card = cache.get(str(int(ref)))
            if card is not None:
                ordered.append(card)
        return ordered

    async def fetch_filtered(*, tag: str | None, limit: int, order: str | None):
        engine = await _ensure_home_engine(container)
        if engine is None:
            return []
        order_clause, asc = _resolve_order_clause(order)
        params = {"limit": int(limit), "fmt": _SQL_DATETIME_FMT}
        if tag:
            params["tag"] = tag
        query = [
            "SELECT n.id",
            "     , n.slug",
            "     , n.title",
            "     , n.author_id::text AS author_id",
            "     , n.is_public",
            "     , n.status",
            "     , COALESCE(array_agg(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL), '{}') AS tags",
            "     , to_char(n.publish_at, :fmt) AS publish_at",
            "     , to_char(n.updated_at, :fmt) AS updated_at",
            "     , n.cover_url",
            "     , n.views_count",
            "     , n.reactions_like_count",
            "  FROM nodes AS n",
            "  LEFT JOIN product_node_tags AS t ON t.node_id = n.id",
            " WHERE n.status <> 'deleted'",
            "   AND n.is_public = TRUE",
        ]
        if tag:
            query.append("   AND t.slug = :tag")
        query.append(
            " GROUP BY n.id, n.slug, n.title, n.author_id, n.is_public, n.status, n.publish_at, n.updated_at, n.cover_url, n.views_count, n.reactions_like_count",
        )
        query.append(f" ORDER BY {order_clause}{' DESC' if not asc else ' ASC'}")
        query.append(" LIMIT :limit")
        sql = "\n".join(query)
        try:
            async with engine.begin() as conn:
                rows = (await conn.execute(text(sql), params)).mappings().all()
        except SQLAlchemyError as exc:  # pragma: no cover - defensive
            logger.warning("home.nodes.query_failed", exc_info=exc)
            return []
        cards: list[dict[str, Any]] = []
        for row in rows:
            cards.append(
                _node_row_to_card(
                    row,
                    tags=list(row.get("tags") or []),
                )
            )
        return cards

    return NodeDataService(fetch_many=fetch_many, fetch_filtered=fetch_filtered)


def _build_quest_data_service(container) -> QuestDataService:
    svc = getattr(container, "quests_service", None)

    async def fetch_many(items: Sequence[str | int]):
        if svc is None:
            return []
        cache: dict[str, dict[str, Any]] = {}
        for item in items:
            ref = str(item)
            if ref in cache:
                continue
            card = _fetch_quest_card(svc, ref)
            if card is None:
                continue
            cache[ref] = card
            cache[str(card.get("id"))] = card
            slug = card.get("slug")
            if isinstance(slug, str):
                cache[slug] = card
        ordered: list[dict[str, Any]] = []
        for item in items:
            ref = str(item)
            card = cache.get(ref)
            if card is not None:
                ordered.append(card)
        return ordered

    async def fetch_filtered(*, tag: str | None, limit: int, order: str | None):
        del order  # unused
        engine = await _ensure_home_engine(container)
        if engine is None:
            return []
        params: dict[str, Any] = {"limit": int(limit)}
        query = [
            "SELECT q.id::text AS id",
            "     , q.slug",
            "     , q.title",
            "     , q.author_id::text AS author_id",
            "     , q.is_public",
            "     , COALESCE(array_agg(DISTINCT qt.slug) FILTER (WHERE qt.slug IS NOT NULL), '{}') AS tags",
            "  FROM quests AS q",
            "  LEFT JOIN quest_tags AS qt ON qt.quest_id = q.id",
            " WHERE q.is_public = TRUE",
        ]
        if tag:
            params["tag"] = tag
            query.append("   AND qt.slug = :tag")
        query.append(" GROUP BY q.id, q.slug, q.title, q.author_id, q.is_public")
        query.append(" ORDER BY q.slug ASC")
        query.append(" LIMIT :limit")
        try:
            async with engine.begin() as conn:
                rows = (
                    (await conn.execute(text("\n".join(query)), params))
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:  # pragma: no cover - defensive
            logger.warning("home.quests.query_failed", exc_info=exc)
            return []
        cards: list[dict[str, Any]] = []
        for row in rows:
            cards.append(
                {
                    "id": row.get("id"),
                    "slug": row.get("slug"),
                    "title": row.get("title"),
                    "authorId": row.get("author_id"),
                    "tags": list(row.get("tags") or []),
                    "isPublic": True,
                }
            )
        return cards

    return QuestDataService(fetch_many=fetch_many, fetch_filtered=fetch_filtered)


def _build_dev_blog_data_service(
    container,
    node_service: NodeDataService,
) -> DevBlogDataService:
    dev_blog_use_case = getattr(container, "_dev_blog_service", None)
    if dev_blog_use_case is None:
        dev_blog_use_case = build_dev_blog_service(container)
        container._dev_blog_service = dev_blog_use_case

    async def fetch_many(items: Sequence[str | int]):
        return await node_service.fetch_by_ids(items)

    async def fetch_filtered(*, tag: str | None, limit: int, order: str | None):
        del tag, order  # unused
        limit_value = max(1, int(limit))
        posts = await dev_blog_use_case.list_latest_for_home(limit=limit_value)
        cards: list[dict[str, Any]] = []
        for post in posts:
            cards.append(
                {
                    "id": str(post.get("id")) if post.get("id") is not None else None,
                    "slug": post.get("slug"),
                    "title": post.get("title"),
                    "summary": post.get("summary"),
                    "coverUrl": post.get("cover_url"),
                    "publishAt": post.get("publish_at"),
                    "updatedAt": post.get("updated_at"),
                    "author": post.get("author"),
                }
            )
        return cards

    return DevBlogDataService(fetch_many=fetch_many, fetch_filtered=fetch_filtered)


def _node_row_to_card(row: Mapping[str, Any], *, tags: list[str]) -> dict[str, Any]:
    return {
        "id": str(row.get("id")),
        "slug": row.get("slug"),
        "title": row.get("title"),
        "authorId": row.get("author_id"),
        "tags": [str(tag) for tag in tags],
        "isPublic": bool(row.get("is_public")),
        "status": row.get("status"),
        "publishAt": row.get("publish_at"),
        "updatedAt": row.get("updated_at"),
        "coverUrl": row.get("cover_url"),
        "views": int(row.get("views_count") or 0),
        "reactions": int(row.get("reactions_like_count") or 0),
    }


def _resolve_order_clause(order: str | None) -> tuple[str, bool]:
    if not order:
        return "COALESCE(n.publish_at, n.updated_at)", False
    normalized = order.strip().lower()
    if normalized in {"publish_at_desc", "published_desc", "publish_desc"}:
        return "n.publish_at", False
    if normalized in {"publish_at_asc", "published_asc"}:
        return "n.publish_at", True
    if normalized in {"updated_at_desc", "updated_desc"}:
        return "n.updated_at", False
    if normalized in {"updated_at_asc", "updated_asc"}:
        return "n.updated_at", True
    if normalized == "random":
        return "random()", True
    if normalized in {"views_desc", "views"}:
        return "n.views_count", False
    return "COALESCE(n.publish_at, n.updated_at)", False


async def _fetch_node_card(service, ref: str) -> dict[str, Any] | None:
    view = await _resolve_node_view(service, ref)
    if view is None:
        return None
    return _node_to_card(view)


async def _resolve_node_view(service, ref: str):
    try:
        node_id = int(ref)
    except (TypeError, ValueError):
        node_id = None

    to_view = getattr(service, "_to_view", None)

    if node_id is not None:
        view = await _call_node_repo_fetch(service, "_repo_get_async", node_id, to_view)
        if view is not None:
            return view

    view = await _call_node_repo_fetch(service, "_repo_get_by_slug_async", ref, to_view)
    if view is not None:
        return view

    if node_id is not None:
        try:
            getter = getattr(service, "get", None)
            if callable(getter):
                result = getter(node_id)
                if result is not None:
                    return result
        except Exception:
            pass

    try:
        getter = getattr(service, "get_by_slug", None)
        if callable(getter):
            result = getter(ref)
            if result is not None:
                return result
    except Exception:
        pass

    return None


async def _call_node_repo_fetch(service, attr: str, value, to_view) -> Any:
    getter = getattr(service, attr, None)
    if not callable(getter):
        return None
    try:
        result = getter(value)
        if inspect.isawaitable(result):
            result = await result
        if result is None:
            return None
        if callable(to_view):
            try:
                converted = to_view(result)
            except Exception:
                converted = None
            else:
                if converted is not None:
                    return converted
        return result
    except Exception:
        return None


def _node_to_card(view: Any) -> dict[str, Any]:
    node_id = getattr(view, "id", None)
    slug = getattr(view, "slug", None)
    publish_at = getattr(view, "publish_at", None)
    updated_at = getattr(view, "updated_at", None) or publish_at
    return {
        "id": str(node_id) if node_id is not None else None,
        "slug": slug,
        "title": getattr(view, "title", None),
        "authorId": getattr(view, "author_id", None),
        "tags": list(getattr(view, "tags", []) or []),
        "isPublic": bool(getattr(view, "is_public", False)),
        "status": getattr(view, "status", None),
        "publishAt": publish_at,
        "updatedAt": updated_at,
        "coverUrl": getattr(view, "cover_url", None),
        "views": getattr(view, "views_count", None),
        "reactions": getattr(view, "reactions_like_count", None),
    }


def _fetch_quest_card(service, ref: str) -> dict[str, Any] | None:
    quest = None
    try:
        quest = service.get(ref)
    except Exception:  # pragma: no cover - defensive fallback
        quest = None
    if quest is None:
        getter = getattr(getattr(service, "repo", None), "get_by_slug", None)
        if callable(getter):
            try:
                quest = getter(ref)
            except Exception:  # pragma: no cover - defensive fallback
                quest = None
    if quest is None:
        return None
    return {
        "id": getattr(quest, "id", None),
        "slug": getattr(quest, "slug", None),
        "title": getattr(quest, "title", None),
        "authorId": getattr(quest, "author_id", None),
        "tags": list(getattr(quest, "tags", []) or []),
        "isPublic": bool(getattr(quest, "is_public", False)),
    }


async def _ensure_home_engine(container) -> AsyncEngine | None:
    cached = getattr(container, "_home_engine", None)
    if cached is not None:
        return cached
    try:
        dsn = to_async_dsn(container.settings.database_url)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("home.invalid_database_url", exc_info=exc)
        return None
    if not dsn:
        return None
    try:
        engine = get_async_engine("content-home", url=dsn, future=True)
    except SQLAlchemyError as exc:
        logger.error("home.engine_creation_failed", exc_info=exc)
        return None
    container._home_engine = engine
    return engine


__all__ = ["make_public_router", "get_home_composer"]
