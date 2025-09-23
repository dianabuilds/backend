from __future__ import annotations

import datetime as dt
import secrets
from collections.abc import Mapping
from typing import Any

import jwt

from domains.platform.iam.ports.token_port import TokenPair, TokenPort
from packages.core.config import Settings

_RESERVED_KEYS = {"sub", "typ", "iat", "exp", "jti"}


class JWTTokenAdapter(TokenPort):
    def __init__(self, settings: Settings) -> None:
        self.s = settings

    def _encode(self, payload: dict[str, Any]) -> str:
        return jwt.encode(payload, key=self.s.auth_jwt_secret, algorithm=self.s.auth_jwt_algorithm)

    def issue(self, subject: str, claims: Mapping[str, Any] | None = None) -> TokenPair:
        now = dt.datetime.utcnow()
        access = {
            "sub": subject,
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=int(self.s.auth_jwt_expires_min))).timestamp()),
            "jti": secrets.token_hex(8),
        }
        refresh = {
            "sub": subject,
            "typ": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(
                (now + dt.timedelta(days=int(self.s.auth_jwt_refresh_expires_days))).timestamp()
            ),
            "jti": secrets.token_hex(16),
        }
        extras: dict[str, Any] = {}
        if claims:
            extras = {k: v for k, v in claims.items() if k not in _RESERVED_KEYS}
            access.update(extras)
            refresh.update(extras)
        return TokenPair(access_token=self._encode(access), refresh_token=self._encode(refresh))

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            claims = jwt.decode(
                refresh_token,
                key=self.s.auth_jwt_secret,
                algorithms=[self.s.auth_jwt_algorithm],
                options={"require": ["exp", "sub"], "verify_aud": False},
            )
        except Exception as e:
            raise RuntimeError(f"invalid_refresh_token: {e}") from e
        if claims.get("typ") != "refresh":
            raise RuntimeError("invalid_token_type")
        extras = {k: v for k, v in claims.items() if k not in _RESERVED_KEYS}
        return self.issue(str(claims.get("sub")), claims=extras)


__all__ = ["JWTTokenAdapter"]
