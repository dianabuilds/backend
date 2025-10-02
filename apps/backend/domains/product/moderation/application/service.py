from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domains.platform.events.ports import OutboxPublisher
from domains.product.moderation.application.ports import Repo

JsonDict = dict[str, Any]
JsonDictList = list[JsonDict]


class ModerationService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    async def list(
        self,
        *,
        page: int = 1,
        size: int = 20,
        statuses: Sequence[str] | None = None,
        types: Sequence[str] | None = None,
        queues: Sequence[str] | None = None,
        assignees: Sequence[str] | None = None,
        query: str | None = None,
    ) -> dict[str, Any]:
        return await self.repo.list_cases(
            page=page,
            size=size,
            statuses=statuses,
            types=types,
            queues=queues,
            assignees=assignees,
            query=query,
        )

    async def create(
        self, payload: dict[str, Any], *, author_id: str | None = None
    ) -> dict[str, Any]:
        data = dict(payload)
        data.setdefault("status", str(payload.get("status", "open")) or "open")
        data.setdefault("type", str(payload.get("type", "general")) or "general")
        cid = await self.repo.create_case(data, created_by=author_id)
        try:
            if self.outbox:
                self.outbox.publish(
                    "moderation.case.created.v1",
                    {
                        "id": cid,
                        "type": data.get("type"),
                        "status": data.get("status"),
                        "actor_id": author_id,
                    },
                )
        except Exception:
            pass
        return {"id": cid}

    async def add_note(
        self, case_id: str, note: dict[str, Any], *, author_id: str | None
    ) -> dict[str, Any] | None:
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

    async def get(self, case_id: str) -> dict[str, Any] | None:
        case = await self.repo.get_case(case_id)
        if not case:
            return None
        return await self._build_detail(case_id, case)

    async def update(
        self, case_id: str, payload: dict[str, Any], *, actor_id: str | None = None
    ) -> dict[str, Any] | None:
        updated = await self.repo.update_case(case_id, payload, actor_id=actor_id)
        if not updated:
            return None
        try:
            if self.outbox:
                self.outbox.publish(
                    "moderation.case.updated.v1",
                    {
                        "id": case_id,
                        "actor_id": actor_id,
                        "fields": sorted(payload.keys()),
                    },
                )
        except Exception:
            pass
        return await self._build_detail(case_id, updated)

    async def _build_detail(self, case_id: str, case: dict[str, Any]) -> dict[str, Any]:
        notes = await self.repo.list_notes(case_id)
        repo_events = await self.repo.list_events(case_id)
        detail = dict(case)
        detail["notes"] = notes
        detail["events"] = self._build_events(detail, repo_events, notes)
        detail["links"] = self._build_links(detail)
        return detail

    def _build_events(
        self,
        case: dict[str, Any],
        repo_events: JsonDictList,
        notes: JsonDictList,
    ) -> JsonDictList:
        timeline: JsonDictList = []
        timeline.extend(repo_events)
        created_at = case.get("created_at")
        if created_at and not any(ev.get("type") == "created" for ev in repo_events):
            timeline.append(
                {
                    "id": f"{case['id']}-created",
                    "type": "created",
                    "title": "Case created",
                    "actor": case.get("created_by_user_id"),
                    "created_at": created_at,
                }
            )
        for note in notes:
            timeline.append(
                {
                    "id": f"{note.get('id')}-note",
                    "type": "note",
                    "title": "Note added",
                    "description": note.get("text"),
                    "actor": note.get("author_id"),
                    "created_at": note.get("created_at"),
                }
            )
        timeline.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        return timeline

    def _build_links(self, case: dict[str, Any]) -> JsonDictList:
        links: JsonDictList = []
        case_id = case.get("id")
        if case_id:
            links.append(
                {
                    "label": "Open case",
                    "href": f"/moderation/cases?case={case_id}",
                    "type": "case",
                }
            )
        subject_id = case.get("subject_id")
        subject_type = str(case.get("subject_type") or "").lower()
        if subject_id:
            if subject_type in {"user", "account", "profile"}:
                links.append(
                    {
                        "label": "View user",
                        "href": f"/moderation/users?focus={subject_id}",
                        "type": "user",
                    }
                )
            elif subject_type in {"node", "content", "post"}:
                links.append(
                    {
                        "label": "Open content",
                        "href": f"/nodes/library?focus={subject_id}",
                        "type": "content",
                    }
                )
        return links


__all__ = ["ModerationService"]
