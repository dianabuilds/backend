from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, Protocol

from domains.platform.flags.domain.models import Flag
from domains.platform.flags.ports import FlagStore


class AsyncRedisCommands(Protocol):
    async def get(self, key: str) -> Any: ...

    async def set(self, key: str, value: str) -> Any: ...

    async def sadd(self, key: str, *members: str) -> Any: ...

    async def smembers(self, key: str) -> Iterable[Any]: ...

    async def delete(self, *keys: str) -> Any: ...

    async def srem(self, key: str, *members: str) -> Any: ...


class RedisFlagStore(FlagStore):
    def __init__(self, client: AsyncRedisCommands, prefix: str = "flags") -> None:
        self._r = client
        self._prefix = prefix
        self._index = f"{prefix}:index"

    def _key(self, slug: str) -> str:
        return f"{self._prefix}:{slug}"

    async def get(self, slug: str) -> Flag | None:
        raw = await self._r.get(self._key(slug))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None
        elif isinstance(raw, dict):
            data = raw
        else:
            return None
        try:
            meta_value = data.get("meta")
            if isinstance(meta_value, dict):
                meta = dict(meta_value)
            else:
                meta = None
            return Flag(
                slug=_to_text(data["slug"]),
                enabled=bool(data.get("enabled", True)),
                description=_coerce_optional_str(data.get("description")),
                rollout=int(data.get("rollout", 100)),
                users=_to_str_set(data.get("users")),
                roles=_to_str_set(data.get("roles")),
                segments=_to_str_set(data.get("segments")),
                meta=meta,
            )
        except (KeyError, TypeError, ValueError):
            return None

    async def upsert(self, flag: Flag) -> Flag:
        payload = {
            "slug": flag.slug,
            "enabled": flag.enabled,
            "description": flag.description,
            "rollout": int(flag.rollout),
            "users": sorted(flag.users),
            "roles": sorted(flag.roles),
            "segments": sorted(flag.segments),
            "meta": flag.meta,
        }
        await self._r.set(self._key(flag.slug), json.dumps(payload))
        await self._r.sadd(self._index, flag.slug)
        return flag

    async def delete(self, slug: str) -> None:
        await self._r.delete(self._key(slug))
        await self._r.srem(self._index, slug)

    async def list(self) -> list[Flag]:
        slugs = await self._r.smembers(self._index)
        items: list[Flag] = []
        for slug in _iterable_to_texts(slugs):
            flag = await self.get(slug)
            if flag is not None:
                items.append(flag)
        return items


def _to_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = _to_text(value).strip()
    return text or None


def _to_str_set(values: Iterable[Any] | None) -> set[str]:
    if not values:
        return set()
    result: set[str] = set()
    for value in values:
        text = _to_text(value).strip()
        if text:
            result.add(text)
    return result


def _iterable_to_texts(values: Iterable[Any] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        text = _to_text(value).strip()
        if text:
            result.append(text)
    return result


__all__ = ["RedisFlagStore"]
