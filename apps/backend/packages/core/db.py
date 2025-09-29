from __future__ import annotations

"""Async database engine helpers and FastAPI dependency utilities."""
import ssl
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .config import load_settings, sanitize_async_dsn

EngineKey = tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]

_engine_cache: dict[str, AsyncEngine] = {}
_engine_shared_cache: dict[EngineKey, AsyncEngine] = {}
_engine_alias_to_key: dict[str, EngineKey] = {}
_engine_key_refcounts: dict[EngineKey, int] = {}


_SSL_TRUE = {"1", "true", "yes", "on", "require", "verify-ca", "verify-full"}
_SSL_FALSE = {"0", "false", "no", "off", "disable", "allow", "prefer"}


def _peel_ssl_connect_args(url: str) -> tuple[str, dict[str, Any], dict[str, str]]:
    """Strip SSL toggles from a DSN query string and return connect arguments."""

    parsed = urlparse(url)
    if not parsed.query:
        return url, {}, {}

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

    connect_args: dict[str, Any] = {}
    fingerprint: dict[str, str] = {}
    ssl_context = None

    if cert_path is not None:
        resolved = cert_path.expanduser()
        if not resolved.is_absolute():
            resolved = (Path.cwd() / resolved).resolve()
        ssl_context = ssl.create_default_context(cafile=str(resolved))
        fingerprint["ssl"] = f"context:{resolved}"

    if ssl_context is not None:
        connect_args["ssl"] = ssl_context
    elif ssl_flag is not None:
        connect_args["ssl"] = "require" if ssl_flag else False
        fingerprint["ssl"] = f"flag:{'require' if ssl_flag else 'disable'}"

    return sanitized, connect_args, fingerprint


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
    engine = _engine_cache.get(alias_key)
    if engine is not None:
        return engine

    engine = _engine_shared_cache.get(canonical_key)
    if engine is None:
        engine = create_async_engine(sanitized, **effective_kwargs)
        _engine_shared_cache[canonical_key] = engine

    _engine_cache[alias_key] = engine
    _engine_alias_to_key[alias_key] = canonical_key
    _engine_key_refcounts[canonical_key] = _engine_key_refcounts.get(canonical_key, 0) + 1
    return engine


async def dispose_async_engines(*names: str) -> None:
    """Dispose cached async engines.

    If `names` is empty, all cached engines are disposed.
    """

    if names:
        prefixes = set(names)
        keys = [k for k in list(_engine_cache.keys()) if k.split(":", 1)[0] in prefixes]
    else:
        keys = list(_engine_cache.keys())

    for key in keys:
        engine = _engine_cache.pop(key, None)
        if engine is None:
            continue
        canonical = _engine_alias_to_key.pop(key, None)
        if canonical is None:
            await engine.dispose()
            continue
        remaining = _engine_key_refcounts.get(canonical, 0) - 1
        if remaining <= 0:
            _engine_key_refcounts.pop(canonical, None)
            shared = _engine_shared_cache.pop(canonical, None)
            if shared is not None:
                await shared.dispose()
        else:
            _engine_key_refcounts[canonical] = remaining


async def db_session_dep() -> AsyncIterator[object]:  # pragma: no cover - placeholder
    yield None


__all__ = ["db_session_dep", "dispose_async_engines", "get_async_engine"]
