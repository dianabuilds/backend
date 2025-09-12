from __future__ import annotations

from app.domains.auth.security.passwords import (
    hash_password as get_password_hash,
    verify_password,
)
from app.domains.auth.security.tokens import (
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

    async def create_refresh_token(self, user_id) -> str:
        return await create_refresh_token(user_id)

    def verify_access_token(self, token: str) -> str | None:
        return verify_access_token(token)

    async def verify_refresh_token(self, token: str) -> str | None:
        return await verify_refresh_token(token)
