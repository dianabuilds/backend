from __future__ import annotations

from ..application.ports import IamClient


class IamClientImpl(IamClient):
    """Adapter to IAM (Identity & Access Management) service.

    Replace HTTP/gRPC wiring with a real client. Keep retries/timeouts/circuit-breakers
    and structured logs. Do not implement business logic here.
    """

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self._base_url = base_url
        self._token = token

    async def has_permission(self, user_id: str, permission: str) -> bool:  # type: ignore[override]
        raise NotImplementedError

    async def get_premium_level(self, user_id: str) -> int:  # type: ignore[override]
        raise NotImplementedError

    async def get_tags(self, user_id: str) -> set[str]:  # type: ignore[override]
        raise NotImplementedError
