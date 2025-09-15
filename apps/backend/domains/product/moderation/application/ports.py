from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Repo(Protocol):
    async def list_cases(
        self, *, page: int, size: int, statuses: Sequence[str] | None = None
    ) -> dict: ...

    async def create_case(self, payload: dict) -> str: ...  # returns case_id

    async def add_note(
        self, case_id: str, note: dict, *, author_id: str | None
    ) -> dict | None: ...
