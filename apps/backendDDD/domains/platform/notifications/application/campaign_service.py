from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.backendDDD.domains.platform.notifications.ports import CampaignRepo


@dataclass
class CampaignService:
    repo: CampaignRepo

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        c = await self.repo.upsert(payload)
        return c.__dict__

    async def list(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        rows = await self.repo.list(limit=limit, offset=offset)
        return [r.__dict__ for r in rows]

    async def delete(self, campaign_id: str) -> None:
        await self.repo.delete(campaign_id)


__all__ = ["CampaignService"]
