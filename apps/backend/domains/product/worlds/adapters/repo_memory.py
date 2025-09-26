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
        self._worlds_by_workspace: dict[str, set[str]] = {}
        self._chars: dict[str, Character] = {}
        self._chars_by_world: dict[str, set[str]] = {}

    # Worlds
    def list_worlds(self, workspace_id: str) -> list[WorldTemplate]:
        ids = list(self._worlds_by_workspace.get(workspace_id, set()))
        return [self._worlds[i] for i in ids]

    def get_world(self, world_id: str, workspace_id: str) -> WorldTemplate | None:
        w = self._worlds.get(world_id)
        if not w:
            return None
        return w if w.workspace_id == workspace_id else None

    def create_world(self, workspace_id: str, data: dict, actor_id: str) -> WorldTemplate:
        wid = _uuid()
        w = WorldTemplate(
            id=wid,
            workspace_id=workspace_id,
            title=str(data.get("title") or "").strip(),
            locale=(data.get("locale") or None),
            description=(data.get("description") or None),
            meta=dict(data.get("meta") or {}),
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._worlds[wid] = w
        self._worlds_by_workspace.setdefault(workspace_id, set()).add(wid)
        return w

    def update_world(
        self, world: WorldTemplate, data: dict, workspace_id: str, actor_id: str
    ) -> WorldTemplate:
        if world.workspace_id != workspace_id:
            return world
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

    def delete_world(self, world: WorldTemplate, workspace_id: str) -> None:
        if world.workspace_id != workspace_id:
            return
        self._worlds.pop(world.id, None)
        ids = self._worlds_by_workspace.get(world.workspace_id)
        if ids and world.id in ids:
            ids.remove(world.id)
        # cascade delete characters
        for cid in list(self._chars_by_world.get(world.id, set())):
            self._chars.pop(cid, None)
        self._chars_by_world.pop(world.id, None)

    # Characters
    def list_characters(self, world_id: str, workspace_id: str) -> list[Character]:
        # ensure world belongs to workspace
        w = self._worlds.get(world_id)
        if not w or w.workspace_id != workspace_id:
            return []
        ids = list(self._chars_by_world.get(world_id, set()))
        return [self._chars[i] for i in ids]

    def get_character(self, char_id: str, workspace_id: str) -> Character | None:
        ch = self._chars.get(char_id)
        if not ch:
            return None
        w = self._worlds.get(ch.world_id)
        return ch if (w and w.workspace_id == workspace_id) else None

    def create_character(
        self, world_id: str, workspace_id: str, data: dict, actor_id: str
    ) -> Character:
        w = self._worlds.get(world_id)
        if not w or w.workspace_id != workspace_id:
            raise ValueError("world_not_found")
        cid = _uuid()
        ch = Character(
            id=cid,
            world_id=world_id,
            name=str(data.get("name") or "").strip(),
            role=(data.get("role") or None),
            description=(data.get("description") or None),
            traits=dict(data.get("traits") or {}),
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._chars[cid] = ch
        self._chars_by_world.setdefault(world_id, set()).add(cid)
        return ch

    def update_character(
        self, ch: Character, data: dict, workspace_id: str, actor_id: str
    ) -> Character:
        w = self._worlds.get(ch.world_id)
        if not w or w.workspace_id != workspace_id:
            return ch
        if "name" in data and data["name"] is not None:
            ch.name = str(data["name"]).strip()
        if "role" in data:
            ch.role = data["role"]
        if "description" in data:
            ch.description = data["description"]
        if "traits" in data and data["traits"] is not None:
            ch.traits = dict(data["traits"])  # shallow copy
        ch.updated_by_user_id = actor_id
        ch.updated_at = datetime.now(tz=UTC)
        return ch

    def delete_character(self, ch: Character, workspace_id: str) -> None:
        w = self._worlds.get(ch.world_id)
        if not w or w.workspace_id != workspace_id:
            return
        self._chars.pop(ch.id, None)
        ids = self._chars_by_world.get(ch.world_id)
        if ids and ch.id in ids:
            ids.remove(ch.id)
