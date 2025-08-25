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
):
    """
    Унифицированное создание Redis-клиента с поддержкой TLS (rediss://).

    - Для rediss:// настраивает SSLContext (TLS >= 1.2).
    - Проверку сертификата можно включить REDIS_SSL_VERIFY=true (по умолчанию отключена,
      чтобы избежать проблем с кастомными CA в облачных Redis).
    - Быстрый таймаут подключения, чтобы health-check не «висел».
    """
    if redis is None:
        raise RuntimeError("redis library is not installed")

    kwargs: dict[str, Any] = {
        "decode_responses": decode_responses,
        "socket_connect_timeout": connect_timeout,
    }

    scheme = url.split(":", 1)[0].lower()
    if scheme == "rediss":
        ctx = ssl.create_default_context()
        # Принудительно TLS >= 1.2
        if hasattr(ssl, "TLSVersion"):  # Py3.7+
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        # Управление верификацией сертификата
        verify = os.getenv("REDIS_SSL_VERIFY", "").lower() in {"1", "true", "yes", "on"}
        if not verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl"] = True
        kwargs["ssl_context"] = ctx

    return redis.from_url(url, **kwargs)
