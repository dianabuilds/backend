from __future__ import annotations

import builtins

from domains.platform.flags.domain.models import Flag
from domains.platform.flags.ports import FlagStore


class InMemoryFlagStore(FlagStore):
    def __init__(self) -> None:
        self._data: dict[str, Flag] = {}

    async def get(self, slug: str) -> Flag | None:
        return self._data.get(slug)

    async def upsert(self, flag: Flag) -> Flag:
        self._data[flag.slug] = flag
        return flag

    async def delete(self, slug: str) -> None:
        self._data.pop(slug, None)

    async def list(self) -> builtins.list[Flag]:
        return list(self._data.values())


__all__ = ["InMemoryFlagStore"]
