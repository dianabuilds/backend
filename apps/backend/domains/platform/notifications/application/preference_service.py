from __future__ import annotations

from typing import Any

from domains.platform.notifications.ports import NotificationPreferenceRepo


class PreferenceService:
    def __init__(self, repo: NotificationPreferenceRepo) -> None:
        self._repo = repo

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        return await self._repo.get_preferences(user_id)

    async def set_preferences(self, user_id: str, prefs: dict[str, Any]) -> None:
        await self._repo.set_preferences(user_id, prefs)


__all__ = ["PreferenceService"]
