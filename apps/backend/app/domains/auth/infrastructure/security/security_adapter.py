from __future__ import annotations

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_password,
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

    def verify_access_token(self, token: str) -> str | None:
        return verify_access_token(token)

    def verify_refresh_token(self, token: str) -> str | None:
        return verify_refresh_token(token)
