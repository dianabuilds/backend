from __future__ import annotations

"""Async database engine helpers and FastAPI dependency utilities."""
import ssl
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .config import load_settings, sanitize_async_dsn

_engine_cache: dict[str, AsyncEngine] = {}


_SSL_TRUE = {"1", "true", "yes", "on", "require", "verify-ca", "verify-full"}
_SSL_FALSE = {"0", "false", "no", "off", "disable", "allow", "prefer"}


def _peel_ssl_connect_args(url: str) -> tuple[str, dict[str, Any]]:
    """Strip SSL toggles from a DSN query string and return connect arguments."""

    parsed = urlparse(url)
    if not parsed.query:
        return url, {}

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
    ssl_context = None

    if cert_path is not None:
        resolved = cert_path.expanduser()
        if not resolved.is_absolute():
            resolved = (Path.cwd() / resolved).resolve()
        ssl_context = ssl.create_default_context(cafile=str(resolved))

    if ssl_context is not None:
        connect_args["ssl"] = ssl_context
    elif ssl_flag is not None:
        connect_args["ssl"] = "require" if ssl_flag else False

    return sanitized, connect_args


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
    sanitized, ssl_connect_args = _peel_ssl_connect_args(sanitized)

    effective_kwargs = dict(create_kwargs)
    connect_args = dict(ssl_connect_args)
    if "connect_args" in effective_kwargs and effective_kwargs["connect_args"]:
        existing = dict(effective_kwargs["connect_args"])  # type: ignore[arg-type]
        connect_args.update(existing)
    if connect_args:
        effective_kwargs["connect_args"] = connect_args
    else:
        effective_kwargs.pop("connect_args", None)

    cache_key = (name, sanitized, tuple(sorted(connect_args.items())))
    if not cache:
        return create_async_engine(sanitized, **effective_kwargs)

    key = ":".join(map(str, cache_key))
    engine = _engine_cache.get(key)
    if engine is None:
        engine = create_async_engine(sanitized, **effective_kwargs)
        _engine_cache[key] = engine
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
        if engine is not None:
            await engine.dispose()


async def db_session_dep() -> AsyncIterator[object]:  # pragma: no cover - placeholder
    yield None


__all__ = ["db_session_dep", "dispose_async_engines", "get_async_engine"]
