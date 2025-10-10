from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from jsonschema import Draft7Validator

from domains.product.content.domain import (
    HomeConfig,
    HomeConfigAudit,
    HomeConfigDraftNotFound,
    HomeConfigDuplicateBlockError,
    HomeConfigHistoryEntry,
    HomeConfigSchemaError,
    HomeConfigValidationError,
)
from domains.product.content.schema import load_home_config_schema

from .ports import HomeConfigRepositoryPort


def _as_mapping(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, Mapping):
        return dict(payload)
    raise HomeConfigValidationError("payload_not_mapping")


def _escape_pointer(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def _join_pointer(path: str, segment: str) -> str:
    escaped = _escape_pointer(str(segment))
    if not path:
        return f"/{escaped}"
    return f"{path}/{escaped}"


def _normalize_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _normalize_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json(v) for v in value]
    return value


def _build_patch(
    before: Mapping[str, Any] | None, after: Mapping[str, Any] | None
) -> list[dict[str, Any]]:
    before_data = _normalize_json(_as_mapping(before))
    after_data = _normalize_json(_as_mapping(after))
    return _diff(before_data, after_data, "")


def _diff(before: Any, after: Any, path: str) -> list[dict[str, Any]]:
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        ops: list[dict[str, Any]] = []
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys - after_keys):
            ops.append({"op": "remove", "path": _join_pointer(path, key)})
        for key in sorted(after_keys - before_keys):
            ops.append(
                {"op": "add", "path": _join_pointer(path, key), "value": after[key]}
            )
        for key in sorted(before_keys & after_keys):
            ops.extend(_diff(before[key], after[key], _join_pointer(path, key)))
        return ops
    if isinstance(before, list) and isinstance(after, list):
        if before == after:
            return []
        return [{"op": "replace", "path": path or "", "value": after}]
    return [{"op": "replace", "path": path or "", "value": after}]


@dataclass(slots=True)
class HomeConfigService:
    repository: HomeConfigRepositoryPort
    _validator: Draft7Validator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        schema = load_home_config_schema()
        object.__setattr__(self, "_validator", Draft7Validator(schema))

    async def get_active(self, slug: str) -> HomeConfig | None:
        return await self.repository.get_active(slug)

    async def get_draft(self, slug: str) -> HomeConfig | None:
        return await self.repository.get_draft(slug)

    async def get_history(
        self,
        slug: str,
        *,
        limit: int = 20,
    ) -> list[HomeConfigHistoryEntry]:
        return await self.repository.list_history(slug, limit=limit)

    async def save_draft(
        self,
        slug: str,
        data: Mapping[str, Any] | None,
        *,
        actor: str | None,
    ) -> HomeConfig:
        payload = _as_mapping(data)
        self._validate_payload(payload)
        existing = await self.repository.get_draft(slug)
        if existing is None:
            active = await self.repository.get_active(slug)
            base_id = active.id if active else None
            return await self.repository.create_draft(
                slug,
                payload,
                actor=actor,
                base_config_id=base_id,
            )
        return await self.repository.update_draft(
            existing.id,
            payload,
            actor=actor,
        )

    async def publish(
        self,
        slug: str,
        *,
        actor: str | None,
        actor_team: str | None = None,
        comment: str | None = None,
    ) -> HomeConfig:
        previous = await self.repository.get_active(slug)
        draft = await self.repository.get_draft(slug)
        if draft is None:
            raise HomeConfigDraftNotFound("home_config_draft_not_found")
        self._validate_payload(draft.data)
        published = await self.repository.publish(draft.id, actor=actor)
        diff = _build_patch(previous.data if previous else {}, published.data)
        await self._audit(
            config_id=published.id,
            version=published.version,
            action="publish",
            actor=actor,
            actor_team=actor_team,
            comment=comment,
            data=published.data,
            diff=diff,
        )
        return published

    async def restore_version(
        self,
        slug: str,
        version: int,
        *,
        actor: str | None,
        actor_team: str | None = None,
        comment: str | None = None,
    ) -> HomeConfig:
        current = await self.repository.get_active(slug)
        restored = await self.repository.restore_version(
            slug,
            version,
            actor=actor,
        )
        self._validate_payload(restored.data)
        diff = _build_patch(current.data if current else {}, restored.data)
        await self._audit(
            config_id=restored.id,
            version=version,
            action="restore",
            actor=actor,
            actor_team=actor_team,
            comment=comment,
            data=restored.data,
            diff=diff,
        )
        return restored

    def validate_payload(self, data: Mapping[str, Any] | None) -> dict[str, Any]:
        payload = _as_mapping(data)
        self._validate_payload(payload)
        return payload

    async def add_audit_entry(
        self,
        *,
        config_id: UUID,
        version: int,
        action: str,
        actor: str | None,
        actor_team: str | None = None,
        comment: str | None = None,
        data: Mapping[str, Any] | None,
        diff: list[dict[str, Any]] | None = None,
    ) -> HomeConfigAudit:
        return await self._audit(
            config_id=config_id,
            version=version,
            action=action,
            actor=actor,
            actor_team=actor_team,
            comment=comment,
            data=data,
            diff=diff,
        )

    async def _audit(
        self,
        *,
        config_id: UUID,
        version: int,
        action: str,
        actor: str | None,
        actor_team: str | None,
        comment: str | None,
        data: Mapping[str, Any] | None,
        diff: list[dict[str, Any]] | None,
    ) -> HomeConfigAudit:
        return await self.repository.add_audit(
            config_id=config_id,
            version=version,
            action=action,
            actor=actor,
            actor_team=actor_team,
            comment=comment,
            data=data,
            diff=diff,
        )

    def _validate_payload(self, payload: Mapping[str, Any]) -> None:
        errors = list(self._validator.iter_errors(payload))
        if errors:
            details = [
                {
                    "path": list(error.path),
                    "message": error.message,
                    "validator": error.validator,
                }
                for error in errors
            ]
            raise HomeConfigSchemaError(
                "home_config_schema_invalid",
                details=details,
            )
        blocks = payload.get("blocks")
        if not isinstance(blocks, list):
            return
        ids = [
            str(block.get("id"))
            for block in blocks
            if isinstance(block, Mapping) and block.get("id")
        ]
        duplicates = [item for item, count in Counter(ids).items() if count > 1]
        if duplicates:
            raise HomeConfigDuplicateBlockError(
                "home_config_duplicate_block_ids",
                details=sorted(duplicates),
            )


__all__ = ["HomeConfigService"]
