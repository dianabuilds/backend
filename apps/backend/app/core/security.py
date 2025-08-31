from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.refresh_token_store import (
    MemoryRefreshTokenStore,
    RefreshTokenStore,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=settings.jwt.expiration),
    }
    return jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)


def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.jwt.secret, algorithms=[settings.jwt.algorithm]
        )
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


# Refresh token storage – can be swapped for a distributed backend
_refresh_store: RefreshTokenStore = MemoryRefreshTokenStore()


def set_refresh_token_store(store: RefreshTokenStore) -> None:
    """Allow overriding the refresh token store (e.g. in tests)."""
    global _refresh_store
    _refresh_store = store


def create_refresh_token(user_id) -> str:
    jti = uuid4().hex
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=settings.jwt.refresh_expiration),
    }
    token = jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)
    _refresh_store.set(jti, str(user_id))
    return token


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.jwt.secret, algorithms=[settings.jwt.algorithm]
        )
    except jwt.PyJWTError:
        return None
    jti = payload.get("jti")
    if not jti:
        return None
    sub = _refresh_store.pop(jti)
    if sub is None:
        return None
    return sub
