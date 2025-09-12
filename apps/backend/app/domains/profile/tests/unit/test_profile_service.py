from __future__ import annotations

from uuid import uuid4

import pytest

from app.domains.profile.application.services.profile_service import ProfileService


class _FakeRepo:
    def __init__(self) -> None:
        self.store: dict = {}

    async def get_display(self, user_id):  # type: ignore[override]
        return self.store.get(user_id)

    async def update_fields(self, user_id, data):  # type: ignore[override]
        cur = self.store.get(user_id, {"id": user_id, "userId": user_id})
        cur.update(data)
        self.store[user_id] = cur
        return cur


@pytest.mark.asyncio
async def test_update_and_get_profile() -> None:
    repo = _FakeRepo()
    svc = ProfileService(repo)
    user = uuid4()
    await svc.update(user, {"username": "neo"})
    res = await svc.get(user)
    assert res and res["username"] == "neo"

