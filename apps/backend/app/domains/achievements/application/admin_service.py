from __future__ import annotations

import builtins
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.achievements.application.ports.repository import (
    IAchievementsRepository,
)
from app.domains.achievements.infrastructure.models.achievement_models import (
    Achievement,
)


class AchievementsAdminService:
    def __init__(self, repo: IAchievementsRepository) -> None:
        self._repo = repo

    async def list(self) -> builtins.list[Achievement]:
        return await self._repo.list_achievements()

    async def create(self, db: AsyncSession, data: dict[str, Any], actor_id: UUID) -> Achievement:
        code = (data.get("code") or "").strip()
        if not code:
            raise ValueError("code_required")
        if await self._repo.exists_code(code):
            raise ValueError("code_conflict")
        item = await self._repo.create_achievement(data, actor_id)
        await db.commit()
        return item

    async def update(
        self,
        db: AsyncSession,
        achievement_id: UUID,
        data: dict[str, Any],
        actor_id: UUID,
    ) -> Achievement | None:
        item = await self._repo.get_achievement(achievement_id)
        if not item:
            return None
        code = data.get("code")
        if code is not None:
            code = code.strip()
            if code != item.code and await self._repo.exists_code(code):
                raise ValueError("code_conflict")
            data["code"] = code
        item = await self._repo.update_achievement_fields(item, data, actor_id)
        await db.commit()
        return item

    async def delete(self, db: AsyncSession, achievement_id: UUID) -> bool:
        item = await self._repo.get_achievement(achievement_id)
        if not item:
            return False
        await self._repo.delete_achievement(item)
        await db.commit()
        return True
