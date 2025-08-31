from __future__ import annotations

from app.domains.auth.application.models import AuthTokens
from app.domains.auth.application.ports.hasher import IPasswordHasher
from app.domains.auth.application.ports.tokens import ITokenService
from app.domains.auth.application.ports.user_repo import IUserRepository


class LoginService:
    def __init__(
        self, repo: IUserRepository, hasher: IPasswordHasher, tokens: ITokenService
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._tokens = tokens

    async def login(self, *, email: str, password: str) -> AuthTokens:
        user = await self._repo.get_by_email(email)
        if user is None or not user.password_hash:
            raise ValueError("invalid credentials")
        if not self._hasher.verify(password, user.password_hash):
            raise ValueError("invalid credentials")
        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id)
        return AuthTokens(access=access, refresh=refresh)
