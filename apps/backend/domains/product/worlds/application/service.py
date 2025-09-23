from __future__ import annotations

from typing import Any

from domains.platform.events.ports import OutboxPublisher
from domains.product.worlds.application.ports import Repo
from domains.product.worlds.domain.entities import (
    Character,
    WorldTemplate,
)


class WorldsService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    def list_worlds(self, workspace_id: str) -> list[WorldTemplate]:
        return self.repo.list_worlds(workspace_id)

    def get_world(self, workspace_id: str, world_id: str) -> WorldTemplate | None:
        return self.repo.get_world(world_id, workspace_id)

    def create_world(self, workspace_id: str, data: dict[str, Any], actor_id: str) -> WorldTemplate:
        w = self.repo.create_world(workspace_id, data, actor_id)
        try:
            if self.outbox:
                self.outbox.publish(
                    "world.created.v1",
                    {"id": w.id, "workspace_id": w.workspace_id, "actor_id": actor_id},
                )
        except Exception:
            pass
        return w

    def update_world(
        self, workspace_id: str, world_id: str, data: dict[str, Any], actor_id: str
    ) -> WorldTemplate | None:
        world = self.repo.get_world(world_id, workspace_id)
        if not world:
            return None
        updated = self.repo.update_world(world, data, workspace_id, actor_id)
        try:
            if updated and self.outbox:
                self.outbox.publish(
                    "world.updated.v1",
                    {
                        "id": updated.id,
                        "workspace_id": updated.workspace_id,
                        "actor_id": actor_id,
                    },
                )
        except Exception:
            pass
        return updated

    def delete_world(self, workspace_id: str, world_id: str) -> bool:
        world = self.repo.get_world(world_id, workspace_id)
        if not world:
            return False
        self.repo.delete_world(world, workspace_id)
        try:
            if self.outbox:
                self.outbox.publish(
                    "world.deleted.v1", {"id": world.id, "workspace_id": workspace_id}
                )
        except Exception:
            pass
        return True

    def list_characters(self, world_id: str, workspace_id: str) -> list[Character]:
        return self.repo.list_characters(world_id, workspace_id)

    def create_character(
        self, world_id: str, workspace_id: str, data: dict[str, Any], actor_id: str
    ) -> Character | None:
        # Repo enforces world/workspace matching where needed
        ch = self.repo.create_character(world_id, workspace_id, data, actor_id)
        try:
            if ch and self.outbox:
                self.outbox.publish(
                    "world.character.created.v1",
                    {
                        "id": ch.id,
                        "world_id": ch.world_id,
                        "workspace_id": workspace_id,
                        "actor_id": actor_id,
                    },
                )
        except Exception:
            pass
        return ch

    def update_character(
        self, char_id: str, workspace_id: str, data: dict[str, Any], actor_id: str
    ) -> Character | None:
        ch = self.repo.get_character(char_id, workspace_id)
        if not ch:
            return None
        out = self.repo.update_character(ch, data, workspace_id, actor_id)
        try:
            if out and self.outbox:
                self.outbox.publish(
                    "world.character.updated.v1",
                    {
                        "id": out.id,
                        "world_id": out.world_id,
                        "workspace_id": workspace_id,
                        "actor_id": actor_id,
                    },
                )
        except Exception:
            pass
        return out

    def delete_character(self, char_id: str, workspace_id: str) -> bool:
        ch = self.repo.get_character(char_id, workspace_id)
        if not ch:
            return False
        self.repo.delete_character(ch, workspace_id)
        try:
            if self.outbox:
                self.outbox.publish(
                    "world.character.deleted.v1",
                    {
                        "id": ch.id,
                        "world_id": ch.world_id,
                        "workspace_id": workspace_id,
                    },
                )
        except Exception:
            pass
        return True

    def get_character(self, char_id: str, workspace_id: str) -> Character | None:
        return self.repo.get_character(char_id, workspace_id)
