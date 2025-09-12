from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.kernel.adapters import redis as redis_adapter
from app.kernel.adapters.cache import RedisCache, create_memory_cache
from app.kernel.cache import AbstractAsyncCache
from app.kernel.mail import AbstractMailService
from app.kernel.adapters.mail_console import ConsoleMailService, NullMailService
from app.kernel.adapters.mail_smtp import SMTPMailService, SmtpConfig


@dataclass
class Services:
    cache: AbstractAsyncCache
    redis_client: Optional[Any] = None
    mail: Optional[AbstractMailService] = None


def _get(env: Mapping[str, str], key: str, default: Optional[str] = None) -> Optional[str]:
    v = env.get(key)
    return v if v is not None else default


async def build_services(env: Optional[Mapping[str, str]] = None) -> Services:
    env = os.environ if env is None else env

    backend = (_get(env, "CACHE_BACKEND", "memory") or "memory").lower()
    redis_url = _get(env, "REDIS_URL")

    cache: AbstractAsyncCache
    redis_client: Optional[Any] = None

    if backend == "redis":
        if not redis_url:
            raise RuntimeError("CACHE_BACKEND=redis requires REDIS_URL to be set")
        redis_client = redis_adapter.create_async_redis(redis_url)
        cache = RedisCache(redis_client)
    else:
        cache = create_memory_cache()

    mail_backend = (_get(env, "MAIL_BACKEND", "console") or "console").lower()
    if mail_backend == "smtp":
        host = _get(env, "SMTP_HOST") or "localhost"
        port = int(_get(env, "SMTP_PORT", "25") or "25")
        username = _get(env, "SMTP_USERNAME")
        password = _get(env, "SMTP_PASSWORD")
        use_tls = (_get(env, "SMTP_USE_TLS", "false") or "false").lower() in {"1", "true", "yes"}
        starttls = (_get(env, "SMTP_STARTTLS", "false") or "false").lower() in {"1", "true", "yes"}
        default_sender = _get(env, "SMTP_SENDER")
        timeout = float(_get(env, "SMTP_TIMEOUT", "10.0") or "10.0")
        mail: Optional[AbstractMailService] = SMTPMailService(
            SmtpConfig(
                host=host,
                port=port,
                username=username,
                password=password,
                use_tls=use_tls,
                starttls=starttls,
                default_sender=default_sender,
                timeout=timeout,
            )
        )
    elif mail_backend == "null":
        mail = NullMailService()
    else:
        mail = ConsoleMailService(default_sender=_get(env, "SMTP_SENDER"))

    return Services(cache=cache, redis_client=redis_client, mail=mail)


async def shutdown_services(services: Services) -> None:
    try:
        await services.cache.close()
    finally:
        if services.redis_client is not None:
            # Best effort close (may be sync or async)
            close = getattr(services.redis_client, "close", None)
            if callable(close):
                res = close()
                if hasattr(res, "__await__"):
                    await res
        if services.mail is not None:
            await services.mail.close()


__all__ = ["Services", "build_services", "shutdown_services"]

