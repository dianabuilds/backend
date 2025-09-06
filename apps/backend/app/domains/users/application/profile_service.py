from __future__ import annotations

from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domains.users.infrastructure.models.user_profile import UserProfile
from app.domains.users.infrastructure.repositories.user_profile_repository import (
    UserProfileRepository,
)


class ProfileService:
    def __init__(self, repo: UserProfileRepository) -> None:
        self._repo = repo

    def _validate_timezone(self, tz: str | None) -> None:
        if tz:
            try:
                ZoneInfo(tz)
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid timezone") from exc

    def _validate_locale(self, locale: str | None) -> None:
        if locale and len(locale) > 10:
            raise ValueError("Invalid locale")

    async def get_profile(self, user_id: UUID) -> UserProfile:
        return await self._repo.get_or_create(user_id)

    async def update_profile(self, user_id: UUID, data: dict[str, Any]) -> UserProfile:
        self._validate_timezone(data.get("timezone"))
        self._validate_locale(data.get("locale"))
        return await self._repo.update_profile(user_id, data)

    async def get_settings(self, user_id: UUID) -> dict[str, Any]:
        profile = await self._repo.get_or_create(user_id)
        return {"preferences": profile.preferences or {}}

    async def update_settings(self, user_id: UUID, prefs: dict[str, Any]) -> dict[str, Any]:
        profile = await self._repo.merge_preferences(user_id, prefs)
        return {"preferences": profile.preferences}
