from __future__ import annotations

import logging
from typing import Any

from domains.platform.events.application.publisher import OutboxPublisher
from domains.product.moderation.application.interactors.cases import (
    ModerationCaseCreateCommand,
    ModerationCaseFilters,
    ModerationCaseNoteCommand,
    ModerationCaseUpdateCommand,
)
from domains.product.moderation.application.interactors.events import (
    ModerationEvent,
    ModerationEventPublisher,
)
from domains.product.moderation.application.ports import Repo
from packages.core import with_trace

logger = logging.getLogger(__name__)

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]


_OUTBOX_EXPECTED_ERRORS = (ValueError, RuntimeError, RedisError)

JsonDict = dict[str, Any]
JsonDictList = list[JsonDict]


class ModerationService:
    def __init__(
        self,
        repo: Repo,
        outbox: OutboxPublisher | None = None,
        event_publisher: ModerationEventPublisher | None = None,
    ):
        self.repo = repo
        self.outbox = outbox
        self._events = event_publisher or ModerationEventPublisher(
            outbox, expected_errors=_OUTBOX_EXPECTED_ERRORS
        )

    def _publish(self, event: str, payload: dict[str, Any]) -> None:
        case_ref = payload.get("id") or payload.get("case_id")
        case_id = str(case_ref) if case_ref else None
        self._events.publish(
            ModerationEvent(
                name=event,
                payload=dict(payload),
                case_id=case_id,
            )
        )

    @with_trace
    async def list(self, filters: ModerationCaseFilters) -> dict[str, Any]:
        normalized = filters.normalized()
        return await self.repo.list_cases(
            page=normalized.page,
            size=normalized.size,
            statuses=normalized.statuses,
            types=normalized.types,
            queues=normalized.queues,
            assignees=normalized.assignees,
            query=normalized.query,
        )

    @with_trace
    async def create(self, command: ModerationCaseCreateCommand) -> dict[str, Any]:
        data = command.to_repo_payload()
        cid = await self.repo.create_case(data, created_by=command.author_id)
        self._publish(
            "moderation.case.created.v1",
            {
                "id": cid,
                "type": data.get("type"),
                "status": data.get("status"),
                "actor_id": command.author_id,
            },
        )
        return {"id": cid}

    @with_trace
    async def add_note(
        self, command: ModerationCaseNoteCommand
    ) -> dict[str, Any] | None:
        payload = command.to_repo_payload()
        result = await self.repo.add_note(
            command.case_id, payload, author_id=command.author_id
        )
        if result:
            self._publish(
                "moderation.case.note_added.v1",
                {"case_id": command.case_id, "author_id": command.author_id},
            )
        return result

    @with_trace
    async def get(self, case_id: str) -> dict[str, Any] | None:
        case = await self.repo.get_case(case_id)
        if not case:
            return None
        return await self._build_detail(case_id, case)

    @with_trace
    async def update(
        self, command: ModerationCaseUpdateCommand
    ) -> dict[str, Any] | None:
        payload = command.to_repo_payload()
        updated = await self.repo.update_case(
            command.case_id, payload, actor_id=command.actor_id
        )
        if not updated:
            return None
        self._publish(
            "moderation.case.updated.v1",
            {
                "id": command.case_id,
                "actor_id": command.actor_id,
                "fields": sorted(payload.keys()),
            },
        )
        return await self._build_detail(command.case_id, updated)

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
