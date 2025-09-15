from __future__ import annotations

from typing import Any, Protocol

from domains.platform.notifications.domain.campaign import Campaign


class CampaignRepo(Protocol):
    async def upsert(self, payload: dict[str, Any]) -> Campaign: ...
    async def list(self, limit: int = 50, offset: int = 0) -> list[Campaign]: ...
    async def get(self, campaign_id: str) -> Campaign | None: ...
    async def delete(self, campaign_id: str) -> None: ...


__all__ = ["CampaignRepo"]
