from __future__ import annotations

import uuid
from datetime import UTC, datetime

from domains.product.worlds.application.ports import Repo
from domains.product.worlds.domain.entities import (
    Character,
    WorldTemplate,
)


def _uuid() -> str:
    return str(uuid.uuid4())


class MemoryRepo(Repo):
    def __init__(self) -> None:
        self._worlds: dict[str, WorldTemplate] = {}
        self._chars: dict[str, Character] = {}
        self._chars_by_world: dict[str, set[str]] = {}

    # Worlds
    def list_worlds(self) -> list[WorldTemplate]:
        return list(self._worlds.values())

    def get_world(self, world_id: str) -> WorldTemplate | None:
        return self._worlds.get(world_id)

    def create_world(self, data: dict, actor_id: str) -> WorldTemplate:
        wid = _uuid()
        world = WorldTemplate(
            id=wid,
            title=str(data.get("title") or "").strip(),
            locale=(data.get("locale") or None),
            description=str(data.get("description") or "").strip(),
            meta=dict(data.get("meta") or {}),
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._worlds[wid] = world
        return world

    def update_world(
        self, world: WorldTemplate, data: dict, actor_id: str
    ) -> WorldTemplate:
        if "title" in data and data["title"] is not None:
            world.title = str(data["title"]).strip()
        if "locale" in data:
            world.locale = data["locale"]
        if "description" in data:
            world.description = data["description"]
        if "meta" in data and data["meta"] is not None:
            world.meta = dict(data["meta"])  # shallow copy
        world.updated_by_user_id = actor_id
        world.updated_at = datetime.now(tz=UTC)
        return world

    def delete_world(self, world: WorldTemplate) -> None:
        self._worlds.pop(world.id, None)
        for cid in list(self._chars_by_world.get(world.id, set())):
            self._chars.pop(cid, None)
        self._chars_by_world.pop(world.id, None)

    # Characters
    def list_characters(self, world_id: str) -> list[Character]:
        if world_id not in self._worlds:
            return []
        ids = list(self._chars_by_world.get(world_id, set()))
        return [self._chars[i] for i in ids]

    def get_character(self, char_id: str) -> Character | None:
        return self._chars.get(char_id)

    def create_character(self, world_id: str, data: dict, actor_id: str) -> Character:
        if world_id not in self._worlds:
            raise ValueError("world_not_found")
        cid = _uuid()
        ch = Character(
            id=cid,
            world_id=world_id,
            name=str(data.get("name") or "").strip(),
            role=(data.get("role") or None),
            description=str(data.get("description") or "").strip(),
            traits=dict(data.get("traits") or {}),
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._chars[cid] = ch
        self._chars_by_world.setdefault(world_id, set()).add(cid)
        return ch

    def update_character(self, ch: Character, data: dict, actor_id: str) -> Character:
        if ch.world_id not in self._worlds:
            return ch
        if "name" in data and data["name"] is not None:
            ch.name = str(data["name"]).strip()
        if "role" in data:
            ch.role = data["role"]
        if "description" in data:
            raw_desc = data["description"]
            ch.description = str(raw_desc or "").strip()
        if "traits" in data and data["traits"] is not None:
            ch.traits = dict(data["traits"])  # shallow copy
        ch.updated_by_user_id = actor_id
        ch.updated_at = datetime.now(tz=UTC)
        return ch

    def delete_character(self, ch: Character) -> None:
        self._chars.pop(ch.id, None)
        ids = self._chars_by_world.get(ch.world_id)
        if ids and ch.id in ids:
            ids.remove(ch.id)
