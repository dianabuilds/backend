from __future__ import annotations

from typing import Optional

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.domains.auth.application.ports.hasher import IPasswordHasher
from app.domains.auth.application.ports.tokens import ITokenService


class PasswordHasher(IPasswordHasher):
    def hash(self, plain: str) -> str:
        return get_password_hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)


class TokenService(ITokenService):
    def create_access_token(self, user_id) -> str:
        return create_access_token(user_id)

    def create_refresh_token(self, user_id) -> str:
        return create_refresh_token(user_id)

    def verify_access_token(self, token: str) -> Optional[str]:
        return verify_access_token(token)

    def verify_refresh_token(self, token: str) -> Optional[str]:
        return verify_refresh_token(token)
