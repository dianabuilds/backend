from __future__ import annotations

from domains.product.profile.domain.entities import Profile


class MemoryRepo:
    def __init__(self):
        self._mem: dict[str, Profile] = {}

    def get(self, id: str) -> Profile | None:  # noqa: A002 - demo name
        return self._mem.get(id)

    def upsert(self, p: Profile) -> Profile:
        self._mem[p.id] = p
        return p
