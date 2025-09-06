from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.infrastructure.models.user_profile import UserProfile


class UserProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create(self, user_id: UUID) -> UserProfile:
        profile = await self._db.get(UserProfile, user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self._db.add(profile)
            await self._db.flush()
        return profile

    async def update_profile(self, user_id: UUID, data: dict[str, Any]) -> UserProfile:
        profile = await self.get_or_create(user_id)
        for field, value in data.items():
            setattr(profile, field, value)
        await self._db.commit()
        await self._db.refresh(profile)
        return profile

    async def merge_preferences(self, user_id: UUID, prefs: dict[str, Any]) -> UserProfile:
        profile = await self.get_or_create(user_id)
        current = dict(profile.preferences or {})
        current.update(prefs or {})
        profile.preferences = current
        await self._db.commit()
        await self._db.refresh(profile)
        return profile
