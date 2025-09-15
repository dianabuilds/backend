from __future__ import annotations

from typing import Any

from apps.backendDDD.domains.platform.events.ports import OutboxPublisher
from apps.backendDDD.domains.product.achievements.application.ports import Repo


class AchievementsService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    async def list(self, user_id: str):
        # synchronous repo; keep API async-friendly
        return list(self.repo.list_for_user(user_id))

    async def grant_manual(self, user_id: str, achievement_id: str) -> bool:
        ok = self.repo.grant(user_id, achievement_id)
        try:
            if ok and self.outbox:
                self.outbox.publish(
                    "achievement.granted.v1",
                    {"user_id": user_id, "achievement_id": achievement_id},
                )
        except Exception:
            pass
        return ok

    async def revoke_manual(self, user_id: str, achievement_id: str) -> bool:
        ok = self.repo.revoke(user_id, achievement_id)
        try:
            if ok and self.outbox:
                self.outbox.publish(
                    "achievement.revoked.v1",
                    {"user_id": user_id, "achievement_id": achievement_id},
                )
        except Exception:
            pass
        return ok


class AchievementsAdminService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    async def list(self):
        return self.repo.list_all()

    async def create(self, data: dict[str, Any], actor_id: str) -> Any:
        code = (data.get("code") or "").strip()
        if not code:
            raise ValueError("code_required")
        if self.repo.exists_code(code):
            raise ValueError("code_conflict")
        payload = dict(data)
        payload["created_by_user_id"] = actor_id
        payload["updated_by_user_id"] = actor_id
        res = self.repo.create(payload)
        try:
            if self.outbox:
                self.outbox.publish(
                    "achievement.created.v1",
                    {"id": res.id, "code": res.code, "title": res.title},
                )
        except Exception:
            pass
        return res

    async def update(self, achievement_id: str, data: dict[str, Any], actor_id: str):
        if "code" in data and data["code"] is not None:
            _code = str(data["code"]).strip()
            # conflict if another achievement already has this code
            # repo.update returns None in case of conflict or not found
        payload = dict(data)
        payload["updated_by_user_id"] = actor_id
        updated = self.repo.update(achievement_id, payload)
        try:
            if updated and self.outbox:
                self.outbox.publish(
                    "achievement.updated.v1",
                    {"id": achievement_id, "fields": list(data.keys())},
                )
        except Exception:
            pass
        if updated is None and ("code" in data and data["code"] is not None):
            # assume conflict
            raise ValueError("code_conflict")
        return updated

    async def delete(self, achievement_id: str) -> bool:
        ok = self.repo.delete(achievement_id)
        try:
            if ok and self.outbox:
                self.outbox.publish("achievement.deleted.v1", {"id": achievement_id})
        except Exception:
            pass
        return ok
