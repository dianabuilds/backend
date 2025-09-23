from __future__ import annotations

import pytest

from domains.platform.notifications.adapters.repo_sql import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)


class MemoryPrefRepo(SQLNotificationPreferenceRepo):
    def __init__(self):
        self._storage: dict[str, dict[str, dict[str, object]]] = {}

    async def get_preferences(self, user_id: str) -> dict[str, object]:
        return self._storage.get(user_id, {})

    async def set_preferences(self, user_id: str, prefs: dict[str, object]) -> None:
        self._storage[user_id] = prefs


@pytest.mark.asyncio
async def test_set_and_get_preferences():
    repo = MemoryPrefRepo()
    service = PreferenceService(repo)

    user_id = "u1"
    prefs = {
        "security": {
            "inapp": {"opt_in": True, "digest": "none", "quiet_hours": []},
            "email": {"opt_in": False, "digest": "none", "quiet_hours": []},
        }
    }

    await service.set_preferences(user_id, prefs)

    saved = await service.get_preferences(user_id)
    assert saved == prefs
