from __future__ import annotations

import builtins
import json

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.flags.domain.models import Flag
from apps.backendDDD.domains.platform.flags.ports import FlagStore


class RedisFlagStore(FlagStore):
    def __init__(self, client: redis.Redis, prefix: str = "flags") -> None:
        self._r = client
        self._prefix = prefix
        self._index = f"{prefix}:index"

    def _key(self, slug: str) -> str:
        return f"{self._prefix}:{slug}"

    async def get(self, slug: str) -> Flag | None:
        raw = await self._r.get(self._key(slug))
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return Flag(
                slug=data["slug"],
                enabled=bool(data.get("enabled", True)),
                description=data.get("description"),
                rollout=int(data.get("rollout", 100)),
                users=set(data.get("users") or ()),
                roles=set(data.get("roles") or ()),
                meta=data.get("meta"),
            )
        except Exception:
            return None

    async def upsert(self, flag: Flag) -> Flag:
        payload = {
            "slug": flag.slug,
            "enabled": flag.enabled,
            "description": flag.description,
            "rollout": int(flag.rollout),
            "users": sorted(flag.users),
            "roles": sorted(flag.roles),
            "meta": flag.meta,
        }
        await self._r.set(self._key(flag.slug), json.dumps(payload))
        await self._r.sadd(self._index, flag.slug)
        return flag

    async def delete(self, slug: str) -> None:
        await self._r.delete(self._key(slug))
        await self._r.srem(self._index, slug)

    async def list(self) -> builtins.list[Flag]:
        slugs = await self._r.smembers(self._index)
        items: list[Flag] = []
        for s in slugs or []:
            f = await self.get(str(s))
            if f:
                items.append(f)
        return items


__all__ = ["RedisFlagStore"]
