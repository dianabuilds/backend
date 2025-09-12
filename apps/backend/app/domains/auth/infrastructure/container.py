from __future__ import annotations

from punq import Container

from app.kernel.config import Settings


def register_auth_providers(container: Container, settings: Settings) -> None:
    """Register Auth domain providers in the DI container.

    Binds application ports to infrastructure adapters. This keeps APIs
    importing only protocols from ``application.ports`` and resolving concrete
    implementations via the container.
    """

    # Password hasher and token services (security adapters)
    from app.domains.auth.application.ports.hasher import IPasswordHasher
    from app.domains.auth.infrastructure.security.security_adapter import (
        PasswordHasher,
        TokenService as TokensAdapter,
    )
    from app.domains.auth.application.ports.tokens import (
        ITokenService as ITokensPort,
    )

    # Rate limiter adapter
    from app.domains.auth.application.ports.ratelimit_port import IRateLimiter
    from app.domains.auth.infrastructure.ratelimit_adapter import CoreRateLimiter

    # Mailer
    from app.domains.auth.application.ports.mail_port import IMailer
    from app.domains.auth.infrastructure.mail_adapter import LegacyMailAdapter
    from app.domains.auth.infrastructure.nonce_store import NonceStore
    from app.domains.auth.infrastructure.verification_token_store import (
        VerificationTokenStore,
    )
    from app.domains.auth.infrastructure.password_reset_store import PasswordResetStore
    from app.providers.redis_utils import create_async_redis

    container.register(IPasswordHasher, PasswordHasher)
    container.register(ITokensPort, TokensAdapter)
    container.register(IRateLimiter, CoreRateLimiter)
    container.register(IMailer, LegacyMailAdapter)

    # Redis client + domain stores (singleton-ish via closure)
    url = settings.redis_url or "fakeredis://"
    try:
        _redis = create_async_redis(url, decode_responses=True)
    except Exception:
        if not url.startswith("fakeredis://"):
            # best-effort fallback to fakeredis when real redis unavailable
            _redis = create_async_redis("fakeredis://", decode_responses=True)
        else:
            raise

    _nonce_store = NonceStore(_redis, settings.auth.nonce_ttl)
    _verification_store = VerificationTokenStore(
        _redis, settings.auth.verification_token_ttl
    )
    _reset_store = PasswordResetStore(_redis, settings.auth.reset_token_ttl)
    container.register(NonceStore, lambda: _nonce_store)
    container.register(VerificationTokenStore, lambda: _verification_store)
    container.register(PasswordResetStore, lambda: _reset_store)
    # Hook Redis refresh token store into token module (optional)
    try:
        from app.domains.auth.infrastructure.refresh_token_store import (
            RedisRefreshTokenStore,
        )
        from app.domains.auth.security.tokens import set_refresh_token_store

        set_refresh_token_store(
            RedisRefreshTokenStore(_redis, ttl=settings.jwt.refresh_expiration)
        )
    except Exception:
        pass


__all__ = ["register_auth_providers"]
