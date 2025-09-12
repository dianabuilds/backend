from __future__ import annotations

from typing import Protocol


class IExampleRepository(Protocol):
    async def get_name(self, id_: int) -> str | None:  # pragma: no cover - contract
        ...

