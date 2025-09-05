from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.user_pref_models import UserAIPref


class UserAIPrefRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, user_id: UUID) -> UserAIPref | None:
        res = await self._db.execute(select(UserAIPref).where(UserAIPref.user_id == user_id))
        return res.scalars().first()

    async def set(self, user_id: UUID, model: str) -> UserAIPref:
        pref = await self.get(user_id)
        if pref:
            pref.model = model
        else:
            pref = UserAIPref(user_id=user_id, model=model)
            self._db.add(pref)
        await self._db.flush()
        return pref


__all__ = ["UserAIPrefRepository"]
