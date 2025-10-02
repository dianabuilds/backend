from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from domains.product.moderation.application.ports import Repo


def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _normalize_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


class MemoryModerationRepo(Repo):
    def __init__(self) -> None:
        # case_id -> dict
        self._cases: dict[str, dict] = {}
        # notes: case_id -> list[dict]
        self._notes: dict[str, list[dict]] = {}
        # events: case_id -> list[dict]
        self._events: dict[str, list[dict]] = {}

    async def list_cases(
        self,
        *,
        page: int,
        size: int,
        statuses: Sequence[str] | None = None,
        types: Sequence[str] | None = None,
        queues: Sequence[str] | None = None,
        assignees: Sequence[str] | None = None,
        query: str | None = None,
    ) -> dict:
        page = max(1, int(page or 1))
        size = max(1, min(int(size or 20), 500))
        items = list(self._cases.values())

        if statuses:
            statuses_set = {str(s).lower() for s in statuses}
            items = [
                c for c in items if str(c.get("status", "")).lower() in statuses_set
            ]
        if types:
            types_set = {str(t).lower() for t in types}
            items = [c for c in items if str(c.get("type", "")).lower() in types_set]
        if queues:
            queues_set = {str(q).lower() for q in queues}
            items = [c for c in items if str(c.get("queue", "")).lower() in queues_set]
        if assignees:
            assignees_set = {str(a) for a in assignees}
            items = [c for c in items if str(c.get("assignee_id")) in assignees_set]
        if query:
            needle = str(query).strip().lower()
            if needle:
                items = [
                    c
                    for c in items
                    if needle
                    in " ".join(
                        str(c.get(field, ""))
                        for field in ("title", "description", "subject_id", "id")
                    ).lower()
                ]

        items.sort(
            key=lambda c: c.get("_created_at") or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        total = len(items)
        start = (page - 1) * size
        slice_ = items[start : start + size]
        prepared: list[dict] = []
        for item in slice_:
            data = {k: v for k, v in item.items() if not k.startswith("_")}
            data.setdefault("created_at", _to_iso(item.get("_created_at")))
            data.setdefault("updated_at", _to_iso(item.get("_updated_at")))
            prepared.append(data)
        return {"items": prepared, "total": total, "page": page, "size": size}

    async def create_case(self, payload: dict, *, created_by: str | None = None) -> str:
        cid = str(uuid.uuid4())
        now = datetime.now(UTC)
        created_at_dt = _normalize_iso(payload.get("created_at")) or now
        updated_at_dt = _normalize_iso(payload.get("updated_at")) or created_at_dt

        item = {
            "id": cid,
            **dict(payload),
            "status": str(payload.get("status") or "open"),
            "created_at": _to_iso(created_at_dt),
            "updated_at": _to_iso(updated_at_dt),
            "created_by_user_id": created_by,
            "_created_at": created_at_dt,
            "_updated_at": updated_at_dt,
        }
        item.setdefault("type", "general")
        self._cases[cid] = item
        self._notes[cid] = []
        self._events[cid] = [
            {
                "id": str(uuid.uuid4()),
                "type": "created",
                "title": "Case created",
                "actor": created_by,
                "created_at": _to_iso(created_at_dt),
            }
        ]
        return cid

    async def add_note(
        self, case_id: str, note: dict, *, author_id: str | None
    ) -> dict | None:
        if case_id not in self._cases:
            return None
        now = datetime.now(UTC)
        record = {
            "id": str(uuid.uuid4()),
            **dict(note),
            "author_id": author_id,
            "created_at": _to_iso(now),
            "_created_at": now,
        }
        self._notes.setdefault(case_id, []).insert(0, record)
        self._cases[case_id]["_updated_at"] = now
        self._cases[case_id]["updated_at"] = _to_iso(now)
        clone = {k: v for k, v in record.items() if not k.startswith("_")}
        return clone

    async def get_case(self, case_id: str) -> dict | None:
        item = self._cases.get(case_id)
        if not item:
            return None
        data = {k: v for k, v in item.items() if not k.startswith("_")}
        data.setdefault("created_at", _to_iso(item.get("_created_at")))
        data.setdefault("updated_at", _to_iso(item.get("_updated_at")))
        return data

    async def list_notes(self, case_id: str) -> list[dict]:
        notes = self._notes.get(case_id, [])
        prepared: list[dict] = []
        for entry in notes:
            data = {k: v for k, v in entry.items() if not k.startswith("_")}
            prepared.append(data)
        return prepared

    async def list_events(self, case_id: str) -> list[dict]:
        return list(self._events.get(case_id, []))

    async def update_case(
        self, case_id: str, payload: dict, *, actor_id: str | None
    ) -> dict | None:
        item = self._cases.get(case_id)
        if not item:
            return None
        allowed_keys = {
            "title",
            "description",
            "status",
            "type",
            "queue",
            "priority",
            "severity",
            "subject_id",
            "subject_type",
            "subject_label",
            "assignee_id",
            "tags",
            "metadata",
        }
        now = datetime.now(UTC)
        events = self._events.setdefault(case_id, [])
        for key, value in payload.items():
            if key not in allowed_keys:
                continue
            previous = item.get(key)
            if previous != value:
                item[key] = value
                events.insert(
                    0,
                    {
                        "id": str(uuid.uuid4()),
                        "type": f"{key}_changed",
                        "field": key,
                        "from": previous,
                        "to": value,
                        "actor": actor_id,
                        "title": f"{key.replace('_', ' ').title()} updated",
                        "description": f"{previous or '-'} > {value or '-'}",
                        "created_at": _to_iso(now),
                    },
                )
        item["_updated_at"] = now
        item["updated_at"] = _to_iso(now)
        return await self.get_case(case_id)
