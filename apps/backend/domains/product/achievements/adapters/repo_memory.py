from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime

from domains.product.achievements.application.ports import Repo
from domains.product.achievements.domain.entities import (
    Achievement,
    UserAchievement,
)


def _uuid() -> str:
    return str(uuid.uuid4())


class MemoryRepo(Repo):
    def __init__(self) -> None:
        # achievements by id
        self._ach: dict[str, Achievement] = {}
        # user -> ach_id -> UserAchievement
        self._user_map: dict[str, dict[str, UserAchievement]] = {}
        # code -> id
        self._by_code: dict[str, str] = {}

    # User views
    def list_for_user(self, user_id: str) -> Iterable[tuple[Achievement, UserAchievement | None]]:
        owned = self._user_map.get(user_id, {})
        for a in sorted(self._ach.values(), key=lambda x: (x.title or "")):
            yield a, owned.get(a.id)

    def grant(self, user_id: str, achievement_id: str) -> bool:
        if achievement_id not in self._ach:
            return False
        bag = self._user_map.setdefault(user_id, {})
        if achievement_id in bag:
            return False
        bag[achievement_id] = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        return True

    def revoke(self, user_id: str, achievement_id: str) -> bool:
        bag = self._user_map.get(user_id, {})
        if achievement_id not in bag:
            return False
        del bag[achievement_id]
        return True

    # Admin
    def list_all(self) -> list[Achievement]:
        return sorted(self._ach.values(), key=lambda x: (x.title or ""))

    def get(self, achievement_id: str) -> Achievement | None:
        return self._ach.get(achievement_id)

    def exists_code(self, code: str) -> bool:
        return code in self._by_code

    def create(self, data: dict) -> Achievement:
        aid = _uuid()
        a = Achievement(
            id=aid,
            code=str(data.get("code") or "").strip(),
            title=str(data.get("title") or "").strip(),
            description=data.get("description"),
            icon=data.get("icon"),
            visible=bool(data.get("visible", True)),
            condition=dict(data.get("condition") or {}),
            created_by_user_id=data.get("created_by_user_id"),
            updated_by_user_id=data.get("updated_by_user_id"),
        )
        self._ach[aid] = a
        self._by_code[a.code] = aid
        return a

    def update(self, achievement_id: str, data: dict) -> Achievement | None:
        a = self._ach.get(achievement_id)
        if not a:
            return None
        if "code" in data:
            new_code = str(data.get("code") or "").strip()
            if new_code != a.code:
                if new_code in self._by_code:
                    # conflict: handled at service layer typically
                    return None
                del self._by_code[a.code]
                a.code = new_code
                self._by_code[new_code] = a.id
        if "title" in data and data["title"] is not None:
            a.title = str(data["title"]).strip()
        if "description" in data:
            a.description = data["description"]
        if "icon" in data:
            a.icon = data["icon"]
        if "visible" in data:
            a.visible = bool(data["visible"])
        if "condition" in data and data["condition"] is not None:
            a.condition = dict(data["condition"])
        if "updated_by_user_id" in data:
            a.updated_by_user_id = data["updated_by_user_id"]
        a.updated_at = datetime.now(tz=UTC)
        return a

    def delete(self, achievement_id: str) -> bool:
        a = self._ach.pop(achievement_id, None)
        if not a:
            return False
        if a.code in self._by_code:
            del self._by_code[a.code]
        # remove grants
        for bag in self._user_map.values():
            bag.pop(achievement_id, None)
        return True
