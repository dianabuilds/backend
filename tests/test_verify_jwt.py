from datetime import datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.security import verify_jwt
from app.security.exceptions import InvalidTokenError, TokenExpiredError


def _encode(payload: dict, secret: str | None = None) -> str:
    return jwt.encode(
        payload, secret or settings.jwt.secret, algorithm=settings.jwt.algorithm
    )


def test_verify_jwt_valid():
    now = datetime.utcnow()
    token = _encode(
        {"sub": "1", "iat": now, "nbf": now, "exp": now + timedelta(minutes=5)}
    )
    payload = verify_jwt(token)
    assert payload["sub"] == "1"


def test_verify_jwt_invalid_signature():
    now = datetime.utcnow()
    token = _encode(
        {"sub": "1", "iat": now, "nbf": now, "exp": now + timedelta(minutes=5)},
        secret="other",
    )
    with pytest.raises(InvalidTokenError):
        verify_jwt(token)


def test_verify_jwt_expired():
    now = datetime.utcnow() - timedelta(minutes=10)
    token = _encode({"sub": "1", "iat": now, "nbf": now, "exp": now})
    with pytest.raises(TokenExpiredError):
        verify_jwt(token)
