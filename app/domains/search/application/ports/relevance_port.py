from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Tuple, List

from app.schemas.search_settings import RelevancePayload


class IRelevanceRepository(Protocol):
    async def get_active(self) -> Optional[Tuple[int, RelevancePayload, datetime]]:  # pragma: no cover - контракт
        ...

    async def create_default_active(self, *, version: int, payload: RelevancePayload, updated_by: Optional[str]) -> datetime:  # pragma: no cover
        ...

    async def get_max_version(self) -> int:  # pragma: no cover - контракт
        ...

    async def add_version(self, *, version: int, payload: RelevancePayload, checksum: str, created_by: Optional[str]) -> None:  # pragma: no cover
        ...

    async def set_active(self, *, version: int, payload: RelevancePayload, updated_by: Optional[str]) -> datetime:  # pragma: no cover
        ...

    async def get_version_payload(self, *, version: int) -> Optional[RelevancePayload]:  # pragma: no cover
        ...
