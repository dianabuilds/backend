from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Repo(Protocol):
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
    ) -> dict[str, Any]: ...

    async def create_case(
        self, payload: dict[str, Any], *, created_by: str | None = None
    ) -> str: ...

    async def add_note(
        self, case_id: str, note: dict[str, Any], *, author_id: str | None
    ) -> dict[str, Any] | None: ...

    async def get_case(self, case_id: str) -> dict[str, Any] | None: ...

    async def list_notes(self, case_id: str) -> list[dict[str, Any]]: ...

    async def list_events(self, case_id: str) -> list[dict[str, Any]]: ...

    async def update_case(
        self, case_id: str, payload: dict[str, Any], *, actor_id: str | None
    ) -> dict[str, Any] | None: ...
