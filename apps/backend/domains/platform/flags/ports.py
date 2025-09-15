from __future__ import annotations

from typing import Protocol

from domains.platform.flags.domain.models import Flag


class FlagStore(Protocol):
    async def get(self, slug: str) -> Flag | None: ...
    async def upsert(self, flag: Flag) -> Flag: ...
    async def delete(self, slug: str) -> None: ...
    async def list(self) -> list[Flag]: ...


__all__ = ["FlagStore"]
