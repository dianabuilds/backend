from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...domain.dtos import AIRuleDTO
from ...domain.records import AIRuleRecord
from ..common import isoformat_utc, resolve_iso
from ..presenters.dto_builders import ai_rule_to_dto

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


async def create_rule(
    service: PlatformModerationService,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
) -> AIRuleDTO:
    async with service._lock:
        rule = AIRuleRecord(
            id=service._generate_id("air"),
            category=str(body.get("category") or "generic"),
            thresholds=dict(body.get("thresholds") or {}),
            actions=dict(body.get("actions") or {}),
            enabled=bool(body.get("enabled", True)),
            updated_by=actor_id or body.get("updated_by") or "system",
            updated_at=service._now(),
            description=body.get("description"),
            history=[],
        )
        rule.history.append(
            {
                "updated_at": isoformat_utc(rule.updated_at),
                "updated_by": rule.updated_by,
                "changes": {"created": True},
            }
        )
        service._ai_rules[rule.id] = rule
        return ai_rule_to_dto(rule, iso=resolve_iso(service))


async def update_rule(
    service: PlatformModerationService,
    rule_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
) -> AIRuleDTO:
    async with service._lock:
        rule = service._ai_rules.get(rule_id)
        if not rule:
            raise KeyError(rule_id)
        changes: dict[str, Any] = {}
        if "category" in body and body["category"]:
            rule.category = str(body["category"])
            changes["category"] = rule.category
        if "thresholds" in body and body["thresholds"] is not None:
            rule.thresholds = dict(body["thresholds"])
            changes["thresholds"] = rule.thresholds
        if "actions" in body and body["actions"] is not None:
            rule.actions = dict(body["actions"])
            changes["actions"] = rule.actions
        if "enabled" in body:
            rule.enabled = bool(body["enabled"])
            changes["enabled"] = rule.enabled
        if "description" in body:
            rule.description = body.get("description")
            changes["description"] = rule.description
        rule.updated_by = actor_id or body.get("updated_by") or "system"
        rule.updated_at = service._now()
        if changes:
            rule.history.append(
                {
                    "updated_at": isoformat_utc(rule.updated_at),
                    "updated_by": rule.updated_by,
                    "changes": changes,
                }
            )
        return ai_rule_to_dto(rule, iso=resolve_iso(service))


async def delete_rule(service: PlatformModerationService, rule_id: str) -> bool:
    async with service._lock:
        removed = service._ai_rules.pop(rule_id, None)
        return bool(removed)
