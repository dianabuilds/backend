from __future__ import annotations

import logging
from typing import Any

from domains.platform.events.errors import OutboxError
from domains.platform.events.ports import OutboxPublisher
from domains.product.worlds.application.ports import Repo
from domains.product.worlds.domain.entities import (
    Character,
    WorldTemplate,
)

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]


logger = logging.getLogger(__name__)

_OUTBOX_EXPECTED_ERRORS = (ValueError, RuntimeError, RedisError)


class WorldsService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    def _safe_publish(self, topic: str, payload: dict[str, Any]) -> None:
        if not self.outbox:
            return
        extra = {
            "topic": topic,
            "world_id": payload.get("world_id") or payload.get("id"),
        }
        try:
            self.outbox.publish(topic, payload, key=str(payload.get("id")))
        except _OUTBOX_EXPECTED_ERRORS as exc:
            logger.warning("worlds_outbox_publish_failed", extra=extra, exc_info=exc)
        except Exception as exc:  # pragma: no cover - unexpected failure
            logger.exception(
                "worlds_outbox_publish_unexpected", extra=extra, exc_info=exc
            )
            raise OutboxError("worlds_outbox_publish_unexpected", topic=topic) from exc

    def list_worlds(self) -> list[WorldTemplate]:
        return self.repo.list_worlds()

    def get_world(self, world_id: str) -> WorldTemplate | None:
        return self.repo.get_world(world_id)

    def create_world(self, data: dict[str, Any], actor_id: str) -> WorldTemplate:
        world = self.repo.create_world(data, actor_id)
        self._safe_publish(
            "world.created.v1",
            {"id": world.id, "actor_id": actor_id},
        )
        return world

    def update_world(
        self, world_id: str, data: dict[str, Any], actor_id: str
    ) -> WorldTemplate | None:
        world = self.repo.get_world(world_id)
        if not world:
            return None
        updated = self.repo.update_world(world, data, actor_id)
        self._safe_publish(
            "world.updated.v1",
            {"id": updated.id, "actor_id": actor_id},
        )
        return updated

    def delete_world(self, world_id: str) -> bool:
        world = self.repo.get_world(world_id)
        if not world:
            return False
        self.repo.delete_world(world)
        self._safe_publish("world.deleted.v1", {"id": world.id})
        return True

    def list_characters(self, world_id: str) -> list[Character]:
        return self.repo.list_characters(world_id)

    def create_character(
        self, world_id: str, data: dict[str, Any], actor_id: str
    ) -> Character | None:
        character = self.repo.create_character(world_id, data, actor_id)
        if character:
            self._safe_publish(
                "world.character.created.v1",
                {
                    "id": character.id,
                    "world_id": character.world_id,
                    "actor_id": actor_id,
                },
            )
        return character

    def update_character(
        self, char_id: str, data: dict[str, Any], actor_id: str
    ) -> Character | None:
        character = self.repo.get_character(char_id)
        if not character:
            return None
        updated = self.repo.update_character(character, data, actor_id)
        if updated:
            self._safe_publish(
                "world.character.updated.v1",
                {"id": updated.id, "world_id": updated.world_id, "actor_id": actor_id},
            )
        return updated

    def delete_character(self, char_id: str) -> bool:
        character = self.repo.get_character(char_id)
        if not character:
            return False
        self.repo.delete_character(character)
        self._safe_publish(
            "world.character.deleted.v1",
            {"id": character.id, "world_id": character.world_id},
        )
        return True

    def get_character(self, char_id: str) -> Character | None:
        return self.repo.get_character(char_id)
