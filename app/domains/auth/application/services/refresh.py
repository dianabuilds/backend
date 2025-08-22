from __future__ import annotations

from app.domains.auth.application.models import AuthTokens
from app.domains.auth.application.ports.tokens import ITokenService


class RefreshService:
    def __init__(self, tokens: ITokenService) -> None:
        self._tokens = tokens

    async def refresh(self, *, refresh_token: str) -> AuthTokens:
        user_id = self._tokens.verify_refresh_token(refresh_token)
        if not user_id:
            raise ValueError("invalid refresh token")
        access = self._tokens.create_access_token(user_id)
        new_refresh = self._tokens.create_refresh_token(user_id)
        return AuthTokens(access=access, refresh=new_refresh)
