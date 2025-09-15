from __future__ import annotations

import secrets

from domains.platform.iam.ports.token_port import TokenPair, TokenPort


class SimpleTokenAdapter(TokenPort):
    def __init__(self) -> None:
        pass

    def issue(self, subject: str) -> TokenPair:
        return TokenPair(
            access_token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        # No validation in stub; return new pair
        return TokenPair(
            access_token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
        )


__all__ = ["SimpleTokenAdapter"]
