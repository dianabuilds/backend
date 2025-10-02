from __future__ import annotations

"""Async database engine helpers and FastAPI dependency utilities."""
import re
import ssl
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .config import load_settings, sanitize_async_dsn

EngineKey = tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]


class EngineRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._alias_cache: dict[str, AsyncEngine] = {}
        self._canonical_cache: dict[EngineKey, AsyncEngine] = {}
        self._alias_to_key: dict[str, EngineKey] = {}
        self._refcounts: dict[EngineKey, int] = {}

    def get_or_create(
        self,
        alias: str,
        canonical_key: EngineKey,
        factory: Callable[[], AsyncEngine],
    ) -> AsyncEngine:
        with self._lock:
            engine = self._alias_cache.get(alias)
            if engine is not None:
                return engine
            engine = self._canonical_cache.get(canonical_key)
            if engine is None:
                engine = factory()
                self._canonical_cache[canonical_key] = engine
            self._alias_cache[alias] = engine
            self._alias_to_key[alias] = canonical_key
            self._refcounts[canonical_key] = self._refcounts.get(canonical_key, 0) + 1
            return engine

    async def dispose(self, prefixes: tuple[str, ...] | None = None) -> None:
        to_dispose: list[AsyncEngine] = []
        with self._lock:
            if prefixes:
                prefix_set = set(prefixes)
                alias_keys = [
                    key
                    for key in list(self._alias_cache.keys())
                    if key.split(":", 1)[0] in prefix_set
                ]
            else:
                alias_keys = list(self._alias_cache.keys())

            for alias in alias_keys:
                engine = self._alias_cache.pop(alias, None)
                if engine is None:
                    continue
                canonical = self._alias_to_key.pop(alias, None)
                if canonical is None:
                    to_dispose.append(engine)
                    continue
                remaining = self._refcounts.get(canonical, 0) - 1
                if remaining <= 0:
                    self._refcounts.pop(canonical, None)
                    shared = self._canonical_cache.pop(canonical, None)
                    if shared is not None:
                        to_dispose.append(shared)
                else:
                    self._refcounts[canonical] = remaining

        seen: set[int] = set()
        for engine in to_dispose:
            marker = id(engine)
            if marker in seen:
                continue
            seen.add(marker)
            await engine.dispose()


_ENGINE_REGISTRY = EngineRegistry()


_SSL_TRUE = {"1", "true", "yes", "on", "require", "verify-ca", "verify-full"}
_SSL_FALSE = {"0", "false", "no", "off", "disable", "allow", "prefer"}


def _peel_ssl_connect_args(url: str) -> tuple[str, dict[str, Any], dict[str, str]]:
    """Strip SSL toggles from a DSN query string and return connect arguments."""

    parsed = urlparse(url)
    if not parsed.query:
        env_ca = _resolve_env_cert()
        connect_args: dict[str, Any] = {}
        fingerprint: dict[str, str] = {}
        if env_ca is not None:
            context = ssl.create_default_context(cafile=str(env_ca))
            connect_args["ssl"] = context
            fingerprint["ssl"] = f"context:{env_ca}"
        return url, connect_args, fingerprint

    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    filtered: list[tuple[str, str]] = []
    ssl_flag: bool | None = None
    cert_path: Path | None = None

    for key, value in pairs:
        lower = key.lower()
        if lower == "ssl":
            normalized = str(value).strip().lower()
            if normalized in _SSL_TRUE:
                ssl_flag = True
                continue
            if normalized in _SSL_FALSE:
                ssl_flag = False
                continue
        elif lower == "sslmode":
            normalized = str(value).strip().lower()
            if normalized in {"require", "verify-ca", "verify-full"}:
                ssl_flag = True
                continue
            if normalized in {"disable", "allow", "prefer"} and ssl_flag is None:
                ssl_flag = False
                continue
        elif lower == "sslrootcert":
            candidate = str(value).strip()
            if candidate:
                cert_path = Path(candidate)
            continue
        filtered.append((key, value))

    query = urlencode(filtered, doseq=True)
    sanitized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query,
            parsed.fragment,
        )
    )

    env_ca = _resolve_env_cert()
    if cert_path is None and env_ca is not None:
        cert_path = env_ca

    try:
        sanitized = re.sub(
            r"([?&])sslmode=[^&]*(&|$)",
            lambda m: m.group(1) if m.group(2) == "&" else "",
            sanitized,
            flags=re.IGNORECASE,
        )
        sanitized = re.sub(r"[?&]$", "", sanitized)
    except Exception:
        pass

    connect_args_final: dict[str, Any] = {}
    fingerprint_final: dict[str, str] = {}
    ssl_context: ssl.SSLContext | None = None

    if cert_path is not None:
        resolved = cert_path.expanduser()
        if not resolved.is_absolute():
            resolved = (Path.cwd() / resolved).resolve()
        ssl_context = ssl.create_default_context(cafile=str(resolved))
        fingerprint_final["ssl"] = f"context:{resolved}"

    if ssl_context is not None:
        connect_args_final["ssl"] = ssl_context
    elif ssl_flag is not None:
        connect_args_final["ssl"] = "require" if ssl_flag else False
        fingerprint_final["ssl"] = f"flag:{'require' if ssl_flag else 'disable'}"

    return sanitized, connect_args_final, fingerprint_final


def _resolve_env_cert() -> Path | None:
    try:
        cfg = load_settings()
        raw = getattr(cfg, "database_ssl_ca", None)
    except Exception:
        return None
    if not raw:
        return None
    candidate = Path(str(raw)).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    return candidate


def _stable_items(
    mapping: dict[str, Any], overrides: dict[str, str] | None = None
) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    for key in sorted(mapping):
        if overrides and key in overrides:
            items.append((key, overrides[key]))
            continue
        value = mapping[key]
        if isinstance(value, ssl.SSLContext):
            items.append((key, "sslctx"))
        else:
            items.append((key, repr(value)))
    return tuple(items)


def _stable_kwargs(kwargs: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    for key in sorted(kwargs):
        if key == "connect_args":
            continue
        items.append((key, repr(kwargs[key])))
    return tuple(items)


def get_async_engine(
    name: str,
    *,
    url: Any | None = None,
    cache: bool = True,
    **create_kwargs: Any,
) -> AsyncEngine:
    """Return a sanitized async engine.

    Args:
        name: Logical identifier for the engine cache (e.g. "notifications").
        url: Optional DSN. Defaults to APP_DATABASE_URL if omitted.
        cache: Reuse/dispose behaviour. When False, no caching is performed.
        create_kwargs: Extra keyword arguments forwarded to `create_async_engine`.
    """

    raw_url = url if url is not None else load_settings().database_url
    sanitized = sanitize_async_dsn(raw_url)
    sanitized, ssl_connect_args, ssl_fingerprint = _peel_ssl_connect_args(sanitized)

    effective_kwargs = dict(create_kwargs)
    effective_kwargs.setdefault("future", True)
    effective_kwargs.setdefault("pool_pre_ping", True)
    connect_args = dict(ssl_connect_args)
    if "connect_args" in effective_kwargs and effective_kwargs["connect_args"]:
        existing = dict(effective_kwargs["connect_args"])  # type: ignore[arg-type]
        connect_args.update(existing)
    if connect_args:
        effective_kwargs["connect_args"] = connect_args
    else:
        effective_kwargs.pop("connect_args", None)

    overrides: dict[str, str] = {}
    if "ssl" in connect_args:
        ssl_value = connect_args["ssl"]
        if isinstance(ssl_value, ssl.SSLContext):
            overrides["ssl"] = ssl_fingerprint.get("ssl", "sslctx")
        else:
            overrides["ssl"] = repr(ssl_value)

    connect_key = _stable_items(connect_args, overrides=overrides)
    kwargs_key = _stable_kwargs(effective_kwargs)
    canonical_key: EngineKey = (str(sanitized), connect_key, kwargs_key)

    if not cache:
        return create_async_engine(sanitized, **effective_kwargs)

    alias_key = f"{name}:{repr(canonical_key)}"

    def _factory() -> AsyncEngine:
        return create_async_engine(sanitized, **effective_kwargs)

    return _ENGINE_REGISTRY.get_or_create(alias_key, canonical_key, _factory)


async def dispose_async_engines(*names: str) -> None:
    """Dispose cached async engines.

    If `names` is empty, all cached engines are disposed.
    """

    prefixes = tuple(names) if names else None
    await _ENGINE_REGISTRY.dispose(prefixes)


async def db_session_dep() -> AsyncIterator[object]:  # pragma: no cover - placeholder
    yield None


def engine_registry() -> EngineRegistry:
    return _ENGINE_REGISTRY


__all__ = [
    "db_session_dep",
    "dispose_async_engines",
    "engine_registry",
    "get_async_engine",
]
