from __future__ import annotations

from app.domains.auth.application.ports.token_port import ITokenService
from app.core.security import create_access_token, create_refresh_token, verify_access_token


class CoreTokenAdapter(ITokenService):
    def create_access_token(self, subject: str) -> str:
        return create_access_token(subject)

    def create_refresh_token(self, subject: str) -> str:
        return create_refresh_token(subject)

    def verify_access_token(self, token: str) -> str | None:
        try:
            return verify_access_token(token)
        except Exception:
            return None
