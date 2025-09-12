from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4
import asyncio

import jwt

from app.kernel.config import settings


class AsyncRefreshTokenStore:
    async def set(self, jti: str, sub: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def pop(self, jti: str) -> str | None:  # pragma: no cover - interface
        raise NotImplementedError


class MemoryRefreshTokenStore(AsyncRefreshTokenStore):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(self, jti: str, sub: str) -> None:
        self._store[jti] = sub

    async def pop(self, jti: str) -> str | None:
        return self._store.pop(jti, None)


_refresh_store: AsyncRefreshTokenStore = MemoryRefreshTokenStore()


def set_refresh_token_store(store: AsyncRefreshTokenStore) -> None:
    global _refresh_store
    _refresh_store = store


def create_access_token(user_id) -> str:
    payload = {
        "sub": str(user_id),
        "jti": uuid4().hex,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=settings.jwt.expiration),
        "aud": settings.jwt.audience,
        "iss": settings.jwt.issuer,
    }
    return jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)


def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,
            issuer=settings.jwt.issuer,
        )
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


async def create_refresh_token(user_id) -> str:
    jti = uuid4().hex
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=settings.jwt.refresh_expiration),
    }
    token = jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)
    await _refresh_store.set(jti, str(user_id))
    return token


async def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.jwt.secret, algorithms=[settings.jwt.algorithm])
    except jwt.PyJWTError:
        return None
    jti = payload.get("jti")
    if not jti:
        return None
    sub = await _refresh_store.pop(jti)
    if sub is None:
        return None
    return sub


__all__ = [
    "AsyncRefreshTokenStore",
    "MemoryRefreshTokenStore",
    "set_refresh_token_store",
    "create_access_token",
    "verify_access_token",
    "create_refresh_token",
    "verify_refresh_token",
]
