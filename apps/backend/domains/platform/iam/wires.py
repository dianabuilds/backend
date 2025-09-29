from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from domains.platform.iam.adapters.credentials_sql import (
    SQLCredentialsAdapter,
)
from domains.platform.iam.adapters.email_via_notifications import (
    EmailViaNotifications,
)
from domains.platform.iam.adapters.nonce_store_redis import (
    RedisNonceStore,
)
from domains.platform.iam.adapters.token_jwt import JWTTokenAdapter
from domains.platform.iam.adapters.token_simple import (
    SimpleTokenAdapter,
)
from domains.platform.iam.adapters.verification_store_redis import (
    RedisVerificationStore,
)
from domains.platform.iam.application.auth_service import AuthService
from domains.platform.iam.ports.token_port import TokenPort
from packages.core.config import Settings, load_settings, to_async_dsn


@dataclass
class IAMContainer:
    settings: Settings
    service: AuthService


def build_container(settings: Settings | None = None) -> IAMContainer:
    s = settings or load_settings()
    client = redis.from_url(str(s.redis_url), decode_responses=True)
    # Prefer JWT adapter; fall back to simple tokens if something goes wrong
    tokens: TokenPort
    try:
        tokens = JWTTokenAdapter(s)
    except Exception:
        tokens = SimpleTokenAdapter()
    nonces = RedisNonceStore(client)
    verification = RedisVerificationStore(client)
    mail = EmailViaNotifications()
    credentials = SQLCredentialsAdapter(to_async_dsn(s.database_url))
    svc = AuthService(
        tokens=tokens,
        nonces=nonces,
        verification=verification,
        mail=mail,
        credentials=credentials,
        settings=s,
    )
    return IAMContainer(settings=s, service=svc)


__all__ = ["IAMContainer", "build_container"]
