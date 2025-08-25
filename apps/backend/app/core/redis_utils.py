from __future__ import annotations

import os
import ssl
from typing import Any

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
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
    """Create configured Redis client with TLS and pooling support.

    The previous implementation passed ``timeout`` directly to ``redis.from_url``,
    which forwards unknown parameters to the connection constructor. Newer
    versions of redis-py no longer accept ``timeout`` in ``Connection`` and raise
    ``TypeError: Connection.__init__() got an unexpected keyword argument
    'timeout'``.  To keep a blocking pool with a timeout we now build the pool
    explicitly using :class:`redis.asyncio.connection.BlockingConnectionPool` and
    then create the client from that pool.

    Parameters mirror the old helper, but ``pool_timeout`` is applied as the
    pool's blocking timeout.
    """

    if redis is None:
        raise RuntimeError("redis library is not installed")

    # Connection-specific kwargs
    conn_kwargs: dict[str, Any] = {
        "socket_connect_timeout": connect_timeout,
    }

    scheme = url.split(":", 1)[0].lower()
    if scheme == "rediss":
        ctx = ssl.create_default_context()
        if hasattr(ssl, "TLSVersion"):
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        verify = os.getenv("REDIS_SSL_VERIFY", "").lower() in {"1", "true", "yes", "on"}
        if not verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        # redis-py expects an ``ssl_context`` for TLS connections
        conn_kwargs["ssl_context"] = ctx

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
