from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.iam.adapters.email_via_notifications import (
    EmailViaNotifications,
)
from apps.backendDDD.domains.platform.iam.adapters.nonce_store_redis import (
    RedisNonceStore,
)
from apps.backendDDD.domains.platform.iam.adapters.token_jwt import JWTTokenAdapter
from apps.backendDDD.domains.platform.iam.adapters.token_simple import (
    SimpleTokenAdapter,
)
from apps.backendDDD.domains.platform.iam.adapters.verification_store_redis import (
    RedisVerificationStore,
)
from apps.backendDDD.domains.platform.iam.application.auth_service import AuthService
from apps.backendDDD.packages.core.config import Settings, load_settings


@dataclass
class IAMContainer:
    settings: Settings
    service: AuthService


def build_container(settings: Settings | None = None) -> IAMContainer:
    s = settings or load_settings()
    client = redis.from_url(str(s.redis_url), decode_responses=True)
    # Prefer JWT adapter; fall back to simple tokens if something goes wrong
    try:
        tokens = JWTTokenAdapter(s)
    except Exception:
        tokens = SimpleTokenAdapter()
    nonces = RedisNonceStore(client)
    verification = RedisVerificationStore(client)
    mail = EmailViaNotifications()
    svc = AuthService(
        tokens=tokens, nonces=nonces, verification=verification, mail=mail
    )
    return IAMContainer(settings=s, service=svc)


__all__ = ["IAMContainer", "build_container"]
