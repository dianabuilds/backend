from __future__ import annotations

import os
import ssl
from typing import Any

try:  # optional dependency
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


def create_async_redis(
    url: str,
    *,
    decode_responses: bool = True,
    connect_timeout: float = 2.0,
    max_connections: int = 50,
    pool_timeout: float = 5.0,
    health_check_interval: int = 30,
):
    """Create configured Redis client with TLS and pooling.

    Compatible with redis-py >= 4 and the existing codebase usage pattern
    (synchronous factory that returns an async Redis client).
    """

    if url.startswith("fakeredis://"):
        try:  # pragma: no cover
            import fakeredis.aioredis as fakeredis  # type: ignore

            return fakeredis.FakeRedis(decode_responses=decode_responses)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("fakeredis backend requested but not available") from exc

    if redis is None:
        raise RuntimeError("redis library is not installed")

    conn_kwargs: dict[str, Any] = {
        "socket_connect_timeout": connect_timeout,
        "socket_timeout": connect_timeout,
    }

    scheme = url.split(":", 1)[0].lower()
    if scheme == "rediss":
        conn_kwargs["ssl"] = True
        verify = os.getenv("REDIS_SSL_VERIFY", "true").lower() in {"1", "true", "yes", "on"}
        if not verify:
            conn_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
            conn_kwargs["ssl_check_hostname"] = False
        ca_file = os.getenv("REDIS_SSL_CA")
        if ca_file:
            conn_kwargs["ssl_ca_certs"] = ca_file

    pool = redis.BlockingConnectionPool.from_url(
        url,
        max_connections=max_connections,
        timeout=pool_timeout,
        **conn_kwargs,
    )

    return redis.Redis(
        connection_pool=pool,
        decode_responses=decode_responses,
        retry_on_timeout=True,
        health_check_interval=health_check_interval,
    )


__all__ = ["create_async_redis"]

