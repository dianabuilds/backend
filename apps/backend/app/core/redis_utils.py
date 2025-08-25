from __future__ import annotations

import os
import ssl
from typing import Any

try:
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
    """
    Унифицированное создание Redis-клиента с поддержкой TLS (rediss://).

    - Для rediss:// настраивает SSLContext (TLS >= 1.2).
    - Проверку сертификата можно включить REDIS_SSL_VERIFY=true (по умолчанию отключена).
    - Таймаут подключения сокетов, ожидания свободного соединения из пула и период health-check'ов.
    """
    if redis is None:
        raise RuntimeError("redis library is not installed")

    kwargs: dict[str, Any] = {
        "decode_responses": decode_responses,
        "socket_connect_timeout": connect_timeout,
        "retry_on_timeout": True,
        "max_connections": max_connections,
        # timeout — это blocking_timeout пула соединений
        "timeout": pool_timeout,
        "health_check_interval": health_check_interval,
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
        # В redis-py достаточно передать ssl_context, параметр "ssl" у asyncio-connection не поддерживается
        kwargs["ssl_context"] = ctx

    return redis.from_url(url, **kwargs)
