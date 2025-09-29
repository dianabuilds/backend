from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from domains.platform.flags.domain.models import Flag
from domains.platform.flags.ports import FlagStore


def _stable_bucket(user_id: str) -> int:
    h = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    # Map first 8 hex chars to 0..99
    return int(h[:8], 16) % 100


@dataclass
class FlagService:
    store: FlagStore

    async def evaluate(self, slug: str, user: dict[str, Any] | None = None) -> bool:
        f = await self.store.get(slug)
        if not f:
            return False
        return self._eval_flag(f, user or {})

    def _eval_flag(self, flag: Flag, user: dict[str, Any]) -> bool:
        if not flag.enabled:
            return False
        uid = str(user.get("sub") or user.get("user_id") or "")
        role = str(user.get("role") or "").lower()
        if uid and uid in flag.users:
            return True
        if role and role in {r.lower() for r in flag.roles}:
            return True
        if flag.rollout >= 100:
            return True
        if flag.rollout <= 0:
            return False
        if not uid:
            return False
        return _stable_bucket(uid) < int(flag.rollout)

    async def upsert(self, data: dict[str, Any]) -> Flag:
        raw_meta = data.get("meta")
        meta_dict: dict[str, Any] | None = None
        if isinstance(raw_meta, dict):
            meta_dict = dict(raw_meta)
        f = Flag(
            slug=str(data["slug"]).strip(),
            enabled=bool(data.get("enabled", True)),
            description=(str(data.get("description")) if data.get("description") else None),
            rollout=int(data.get("rollout", 100)),
            users=set(map(str, data.get("users") or [])),
            roles=set(map(str, data.get("roles") or [])),
            meta=meta_dict,
        )
        return await self.store.upsert(f)

    async def delete(self, slug: str) -> None:
        await self.store.delete(slug)

    async def list(self) -> list[Flag]:
        return await self.store.list()


__all__ = ["FlagService"]
