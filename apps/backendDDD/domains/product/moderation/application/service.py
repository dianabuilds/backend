from __future__ import annotations

from apps.backendDDD.domains.platform.events.ports import OutboxPublisher
from apps.backendDDD.domains.product.moderation.application.ports import Repo


class ModerationService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    async def list(
        self, *, page: int = 1, size: int = 20, statuses: list[str] | None = None
    ) -> dict:
        return await self.repo.list_cases(page=page, size=size, statuses=statuses)

    async def create(self, payload: dict) -> dict:
        cid = await self.repo.create_case(payload)
        try:
            if self.outbox:
                self.outbox.publish("moderation.case.created.v1", {"id": cid})
        except Exception:
            pass
        return {"id": cid}

    async def add_note(
        self, case_id: str, note: dict, *, author_id: str | None
    ) -> dict | None:
        res = await self.repo.add_note(case_id, note, author_id=author_id)
        try:
            if res and self.outbox:
                self.outbox.publish(
                    "moderation.case.note_added.v1",
                    {"case_id": case_id, "author_id": author_id},
                )
        except Exception:
            pass
        return res
