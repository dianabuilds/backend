"""Home page composer module for assembling the public payload."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any, Protocol

from domains.product.content.domain import HomeConfig

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Counter = Gauge = None  # type: ignore[misc, assignment]

if Counter is not None:
    HOME_CACHE_REQUESTS = Counter(
        "home_cache_requests",
        "Home composer cache lookups",
        labelnames=("result",),
    )
else:
    HOME_CACHE_REQUESTS = None

if Gauge is not None:
    HOME_CACHE_HIT_RATIO = Gauge(
        "home_cache_hit_ratio",
        "Ratio of home composer cache hits to total lookups",
    )
else:
    HOME_CACHE_HIT_RATIO = None

_METRICS_LOCK = Lock()
_CACHE_HITS = 0
_CACHE_TOTAL = 0


def _record_cache_metrics(result: str) -> None:
    global _CACHE_HITS, _CACHE_TOTAL
    if HOME_CACHE_REQUESTS is not None:
        HOME_CACHE_REQUESTS.labels(result=result).inc()
    if result not in {"hit", "miss"}:
        return
    with _METRICS_LOCK:
        if result == "hit":
            _CACHE_HITS += 1
        _CACHE_TOTAL += 1
        ratio = (_CACHE_HITS / _CACHE_TOTAL) if _CACHE_TOTAL else 0.0
    if HOME_CACHE_HIT_RATIO is not None:
        HOME_CACHE_HIT_RATIO.set(ratio)


class DataSourceError(RuntimeError):
    """Raised when a data source fails to provide items."""

    def __init__(self, code: str, *, detail: str | None = None) -> None:
        super().__init__(code)
        self.reason = code
        self.detail = detail


@dataclass(slots=True)
class DataSourceFilter:
    tag: str | None = None
    limit: int | None = None
    order: str | None = None


@dataclass(slots=True)
class DataSourceConfig:
    mode: str
    entity: str
    items: tuple[str | int, ...] = ()
    filter: DataSourceFilter = field(default_factory=DataSourceFilter)


@dataclass(slots=True)
class BlockConfig:
    id: str
    type: str
    enabled: bool
    title: str | None = None
    slots: Mapping[str, Any] | None = None
    layout: Mapping[str, Any] | None = None
    data_source: DataSourceConfig | None = None
    raw: Mapping[str, Any] | None = None


class EntityDataService(Protocol):
    async def fetch_by_ids(
        self, ids: Sequence[str | int]
    ) -> list[Mapping[str, Any]]: ...

    async def fetch_by_filter(
        self, *, tag: str | None, limit: int, order: str | None
    ) -> list[Mapping[str, Any]]: ...


class HomeCache(Protocol):
    async def get(self, key: str) -> Mapping[str, Any] | None: ...

    async def set(
        self, key: str, value: Mapping[str, Any], *, ttl: int | None = None
    ) -> None: ...

    async def invalidate(self, key: str) -> None: ...


@dataclass(slots=True)
class InMemoryHomeCache(HomeCache):
    default_ttl: int | None = None

    def __post_init__(self) -> None:
        self._store: dict[str, tuple[float | None, Mapping[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Mapping[str, Any] | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            now = asyncio.get_running_loop().time()
            if expires_at is not None and expires_at <= now:
                self._store.pop(key, None)
                return None
            return deepcopy(value)

    async def set(
        self, key: str, value: Mapping[str, Any], *, ttl: int | None = None
    ) -> None:
        async with self._lock:
            expire = None
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            if ttl_seconds:
                expire = asyncio.get_running_loop().time() + max(0, ttl_seconds)
            self._store[key] = (expire, deepcopy(value))

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)


@dataclass(slots=True)
class CallableEntityDataService(EntityDataService):
    fetch_many: Callable[[Sequence[str | int]], Awaitable[list[Mapping[str, Any]]]]
    fetch_filtered: Callable[
        [str | None, int, str | None], Awaitable[list[Mapping[str, Any]]]
    ]

    async def fetch_by_ids(self, ids: Sequence[str | int]) -> list[Mapping[str, Any]]:
        return await self.fetch_many(ids)

    async def fetch_by_filter(
        self, *, tag: str | None, limit: int, order: str | None
    ) -> list[Mapping[str, Any]]:
        return await self.fetch_filtered(tag, limit, order)


class NodeDataService(CallableEntityDataService):
    """Data accessor for node cards."""


class QuestDataService(CallableEntityDataService):
    """Data accessor for quest cards."""


class DevBlogDataService(CallableEntityDataService):
    """Data accessor for dev blog cards."""


class DataSourceStrategy(Protocol):
    async def resolve(
        self,
        *,
        block_id: str,
        config: DataSourceConfig,
        service: EntityDataService,
    ) -> list[Mapping[str, Any]]: ...


@dataclass(slots=True)
class ManualSource(DataSourceStrategy):
    timeout: float = 1.0
    logger: logging.Logger = field(default=logger, repr=False)

    async def resolve(
        self,
        *,
        block_id: str,
        config: DataSourceConfig,
        service: EntityDataService,
    ) -> list[Mapping[str, Any]]:
        ids = list(config.items)
        if not ids:
            return []
        try:
            items = await asyncio.wait_for(
                service.fetch_by_ids(ids), timeout=self.timeout
            )
        except TimeoutError as exc:
            self.logger.warning(
                "home.manual_source_timeout", extra={"block_id": block_id}
            )
            raise DataSourceError("timeout") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception(
                "home.manual_source_error", extra={"block_id": block_id}, exc_info=exc
            )
            raise DataSourceError("error", detail=str(exc)) from exc
        normalized: dict[str, Mapping[str, Any]] = {}
        for item in items:
            if not isinstance(item, Mapping):
                continue
            key = _normalize_id(item.get("id"))
            if key is None:
                continue
            normalized.setdefault(key, item)
        resolved: list[Mapping[str, Any]] = []
        missing: list[str | int] = []
        for original in ids:
            key = _normalize_id(original)
            if key and key in normalized:
                resolved.append(normalized[key])
            else:
                missing.append(original)
        if missing:
            self.logger.info(
                "home.manual_source_missing_items",
                extra={
                    "block_id": block_id,
                    "missing": [str(value) for value in missing],
                },
            )
        return resolved


@dataclass(slots=True)
class AutoSource(DataSourceStrategy):
    timeout: float = 1.5
    max_limit: int = 12
    default_limit: int = 6
    logger: logging.Logger = field(default=logger, repr=False)

    async def resolve(
        self,
        *,
        block_id: str,
        config: DataSourceConfig,
        service: EntityDataService,
    ) -> list[Mapping[str, Any]]:
        requested = config.filter.limit or self.default_limit
        if requested <= 0:
            requested = self.default_limit
        limit = min(requested, self.max_limit)
        try:
            items = await asyncio.wait_for(
                service.fetch_by_filter(
                    tag=config.filter.tag,
                    limit=limit,
                    order=config.filter.order,
                ),
                timeout=self.timeout,
            )
        except TimeoutError as exc:
            self.logger.warning(
                "home.auto_source_timeout",
                extra={
                    "block_id": block_id,
                    "limit": limit,
                    "timeout": self.timeout,
                },
            )
            raise DataSourceError("timeout") from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception(
                "home.auto_source_error",
                extra={
                    "block_id": block_id,
                    "limit": limit,
                },
                exc_info=exc,
            )
            raise DataSourceError("error", detail=str(exc)) from exc
        if len(items) > limit:
            return list(items[:limit])
        return items


class HomeComposer:
    """Compose public home page payload using config blocks and data sources."""

    def __init__(
        self,
        *,
        cache: HomeCache,
        node_service: EntityDataService,
        quest_service: EntityDataService,
        dev_blog_service: EntityDataService,
        manual_timeout: float = 1.0,
        auto_timeout: float = 1.5,
        cache_ttl: int = 300,
        cache_prefix: str = "home:public",
        max_auto_items: int = 12,
        default_auto_items: int | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._cache = cache
        self._cache_ttl = cache_ttl
        normalized_prefix = cache_prefix.rstrip(":") if cache_prefix else ""
        self._cache_prefix = normalized_prefix or "home:public"
        self._logger = logger or logging.getLogger(__name__)
        if default_auto_items is None:
            default_auto_items = min(6, max_auto_items) if max_auto_items > 0 else 6
        self._strategies: dict[str, DataSourceStrategy] = {
            "manual": ManualSource(timeout=manual_timeout, logger=self._logger),
            "auto": AutoSource(
                timeout=auto_timeout,
                max_limit=max_auto_items,
                default_limit=max(1, default_auto_items),
                logger=self._logger,
            ),
        }
        self._entities: dict[str, EntityDataService] = {
            "node": node_service,
            "quest": quest_service,
            "dev_blog": dev_blog_service,
        }

    async def compose(
        self,
        config: HomeConfig,
        *,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        cache_key = self._cache_key_for_slug(config.slug)
        cached_payload: Mapping[str, Any] | None = None
        cache_result: str | None = None
        if use_cache:
            if force_refresh:
                await self._cache.invalidate(cache_key)
                cache_result = "miss"
            else:
                cached_payload = await self._cache.get(cache_key)
                if cached_payload is not None:
                    cached_version = cached_payload.get("version")
                    cached_version_int: int | None
                    if isinstance(cached_version, int):
                        cached_version_int = cached_version
                    elif isinstance(cached_version, str):
                        try:
                            cached_version_int = int(cached_version)
                        except ValueError:
                            cached_version_int = None
                    else:
                        cached_version_int = None
                    if cached_version_int == config.version:
                        _record_cache_metrics("hit")
                        return deepcopy(dict(cached_payload))
                cache_result = "miss"
        blocks: list[dict[str, Any]] = []
        fallbacks: list[dict[str, Any]] = []
        for raw_block in _iter_blocks(config.data):
            block_cfg = _build_block_config(raw_block)
            if block_cfg is None:
                continue
            if not block_cfg.enabled:
                fallbacks.append({"id": block_cfg.id, "reason": "disabled"})
                continue
            data_source = block_cfg.data_source
            if data_source is None:
                fallbacks.append({"id": block_cfg.id, "reason": "missing_data_source"})
                continue
            service = self._entities.get(data_source.entity)
            if service is None:
                self._logger.warning(
                    "home.unknown_entity",
                    extra={
                        "block_id": block_cfg.id,
                        "entity": data_source.entity,
                    },
                )
                fallbacks.append(
                    {
                        "id": block_cfg.id,
                        "reason": "unknown_entity",
                        "entity": data_source.entity,
                    }
                )
                continue
            strategy = self._strategies.get(data_source.mode)
            if strategy is None:
                fallbacks.append(
                    {
                        "id": block_cfg.id,
                        "reason": "unknown_mode",
                        "mode": data_source.mode,
                    }
                )
                continue
            try:
                items = await strategy.resolve(
                    block_id=block_cfg.id,
                    config=data_source,
                    service=service,
                )
            except DataSourceError as exc:
                payload = {
                    "id": block_cfg.id,
                    "reason": exc.reason,
                    "mode": data_source.mode,
                    "entity": data_source.entity,
                }
                if exc.detail:
                    payload["detail"] = exc.detail
                fallbacks.append(payload)
                continue
            if not items:
                fallbacks.append(
                    {
                        "id": block_cfg.id,
                        "reason": "empty",
                        "mode": data_source.mode,
                        "entity": data_source.entity,
                    }
                )
                continue
            block_payload: dict[str, Any] = {
                "id": block_cfg.id,
                "type": block_cfg.type,
                "items": items,
                "dataSource": {
                    "mode": data_source.mode,
                    "entity": data_source.entity,
                },
            }
            if block_cfg.title is not None:
                block_payload["title"] = block_cfg.title
            if block_cfg.slots is not None:
                block_payload["slots"] = deepcopy(block_cfg.slots)
            if block_cfg.layout is not None:
                block_payload["layout"] = deepcopy(block_cfg.layout)
            blocks.append(block_payload)
        result: dict[str, Any] = {
            "slug": config.slug,
            "version": config.version,
            "updated_at": _iso_datetime(config.updated_at),
            "published_at": _iso_datetime(config.published_at),
            "generated_at": _iso_datetime(datetime.now(UTC)),
            "blocks": blocks,
            "meta": _ensure_mapping(config.data.get("meta")),
            "fallbacks": fallbacks,
        }
        if use_cache:
            if cache_result is None:
                cache_result = "miss"
            _record_cache_metrics(cache_result)
            await self._cache.set(cache_key, result, ttl=self._cache_ttl)
        return deepcopy(result)

    async def invalidate_slug(self, slug: str | None) -> None:
        await self._cache.invalidate(self._cache_key_for_slug(slug))

    def _cache_key(self, config: HomeConfig) -> str:
        return self._cache_key_for_slug(config.slug)

    def _cache_key_for_slug(self, slug: str | None) -> str:
        normalized = (slug or "main").strip().lower()
        if not normalized:
            normalized = "main"
        prefix = self._cache_prefix or "home:public"
        return f"{prefix}:{normalized}"


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _ensure_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _iter_blocks(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_blocks = payload.get("blocks")
    if not isinstance(raw_blocks, Sequence) or isinstance(raw_blocks, (str, bytes)):
        return []
    items: list[Mapping[str, Any]] = []
    for entry in raw_blocks:
        if isinstance(entry, Mapping):
            items.append(entry)
    return items


def _normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int,)):
        return str(value)
    return str(value)


def _parse_data_source(raw: Any) -> DataSourceConfig | None:
    if not isinstance(raw, Mapping):
        return None
    mode = str(raw.get("mode", "")).strip().lower()
    if mode not in {"manual", "auto"}:
        return None
    entity = str(raw.get("entity", "node")).strip().lower()
    filter_cfg = _parse_filter(raw.get("filter"))
    items: tuple[str | int, ...] = ()
    if mode == "manual":
        items = _coerce_items(raw.get("items"))
    return DataSourceConfig(mode=mode, entity=entity, items=items, filter=filter_cfg)


def _parse_filter(raw: Any) -> DataSourceFilter:
    if not isinstance(raw, Mapping):
        return DataSourceFilter()
    tag_value = raw.get("tag")
    limit_value = raw.get("limit")
    order_value = raw.get("order")
    tag = str(tag_value).strip() if tag_value not in (None, "") else None
    order = str(order_value).strip() if order_value not in (None, "") else None
    limit: int | None
    if isinstance(limit_value, int):
        limit = limit_value
    elif isinstance(limit_value, str):
        try:
            limit = int(limit_value)
        except ValueError:
            limit = None
    else:
        limit = None
    return DataSourceFilter(tag=tag, limit=limit, order=order)


def _coerce_items(raw: Any) -> tuple[str | int, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()
    items: list[str | int] = []
    for value in raw:
        if isinstance(value, (str, int)):
            items.append(value)
        elif value is not None:
            items.append(str(value))
    return tuple(items)


def _build_block_config(raw: Mapping[str, Any]) -> BlockConfig | None:
    block_id = str(raw.get("id") or "").strip()
    block_type = str(raw.get("type") or "").strip()
    if not block_id or not block_type:
        return None
    enabled = bool(raw.get("enabled", False))
    title = raw.get("title")
    if title is not None:
        title = str(title)
    slots = raw.get("slots")
    layout = raw.get("layout")
    slots_dict = dict(slots) if isinstance(slots, Mapping) else None
    layout_dict = dict(layout) if isinstance(layout, Mapping) else None
    data_source = _parse_data_source(raw.get("dataSource"))
    return BlockConfig(
        id=block_id,
        type=block_type,
        enabled=enabled,
        title=title,
        slots=slots_dict,
        layout=layout_dict,
        data_source=data_source,
        raw=raw,
    )


__all__ = [
    "AutoSource",
    "BlockConfig",
    "CallableEntityDataService",
    "DataSourceConfig",
    "DataSourceFilter",
    "DataSourceStrategy",
    "DevBlogDataService",
    "EntityDataService",
    "HomeCache",
    "HomeComposer",
    "InMemoryHomeCache",
    "ManualSource",
    "NodeDataService",
    "QuestDataService",
]
