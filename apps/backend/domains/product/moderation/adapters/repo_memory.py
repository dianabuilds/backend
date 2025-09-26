from __future__ import annotations

import uuid
from collections.abc import Sequence

from domains.product.moderation.application.ports import Repo


class MemoryModerationRepo(Repo):
    def __init__(self) -> None:
        # case_id -> dict
        self._cases: dict[str, dict] = {}
        # notes: case_id -> list[dict]
        self._notes: dict[str, list[dict]] = {}

    async def list_cases(
        self, *, page: int, size: int, statuses: Sequence[str] | None = None
    ) -> dict:
        items = list(self._cases.values())
        if statuses:
            statuses_set = {s.lower() for s in statuses}
            items = [c for c in items if str(c.get("status", "")).lower() in statuses_set]
        total = len(items)
        start = (max(1, page) - 1) * max(1, size)
        slice_ = items[start : start + size]
        return {"items": slice_, "total": total, "page": page, "size": size}

    async def create_case(self, payload: dict) -> str:
        cid = str(uuid.uuid4())
        item = {"id": cid, **dict(payload)}
        item.setdefault("status", "open")
        self._cases[cid] = item
        self._notes[cid] = []
        return cid

    async def add_note(self, case_id: str, note: dict, *, author_id: str | None) -> dict | None:
        if case_id not in self._cases:
            return None
        n = {"id": str(uuid.uuid4()), **dict(note), "author_id": author_id}
        self._notes.setdefault(case_id, []).append(n)
        return n
