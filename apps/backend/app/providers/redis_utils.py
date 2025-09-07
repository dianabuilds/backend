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
    The previous implementation passed deprecated parameters such as ``timeout``
    or ``ssl_context`` directly to ``redis.from_url``, which forwarded them to
    the connection constructor.  redis-py 6 removed these arguments, leading to
    ``TypeError`` during client initialization.  To keep a blocking pool with a
    configurable timeout we now build the pool explicitly using
    :class:`redis.asyncio.connection.BlockingConnectionPool` and translate TLS
    options to the new ``ssl``-based API.

    Parameters mirror the old helper, but ``pool_timeout`` is applied as the
    pool's blocking timeout.
    """

    if url.startswith("fakeredis://"):
        # Lightweight in-memory backend for local/dev and tests
        # Import lazily to avoid hard dependency in production
        try:  # pragma: no cover - exercised in tests
            import fakeredis.aioredis as fakeredis  # type: ignore

            return fakeredis.FakeRedis(decode_responses=decode_responses)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("fakeredis backend requested but not available") from exc

    if redis is None:
        raise RuntimeError("redis library is not installed")

    # Connection-specific kwargs
    conn_kwargs: dict[str, Any] = {
        "socket_connect_timeout": connect_timeout,
        "socket_timeout": connect_timeout,  # не даём операциям зависать
    }

    scheme = url.split(":", 1)[0].lower()
    if scheme == "rediss":
        # Явно включаем TLS на соединении (redis-py учитывает rediss в from_url,
        # но явная установка устраняет неоднозначности в разных версиях).
        conn_kwargs["ssl"] = True
        verify = os.getenv("REDIS_SSL_VERIFY", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not verify:
            conn_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
            conn_kwargs["ssl_check_hostname"] = False
        # Пользователь может указать кастомный корневой сертификат
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
