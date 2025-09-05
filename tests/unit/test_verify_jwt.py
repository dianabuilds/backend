from __future__ import annotations

import os
from datetime import datetime, timedelta

import jwt
import pytest

os.environ["USE_MINIMAL_CONFIG"] = "True"

from app.core.config import settings
from app.core.security import create_access_token
from app.security import InvalidTokenError, verify_jwt


def test_verify_jwt_accepts_valid_token() -> None:
    token = create_access_token("123")
    payload = verify_jwt(token)
    assert payload["sub"] == "123"


def test_verify_jwt_rejects_wrong_audience() -> None:
    wrong_token = jwt.encode(
        {
            "sub": "123",
            "aud": "wrong",
            "iss": settings.jwt.issuer,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=60),
        },
        settings.jwt.secret,
        algorithm=settings.jwt.algorithm,
    )
    with pytest.raises(InvalidTokenError):
        verify_jwt(wrong_token)
