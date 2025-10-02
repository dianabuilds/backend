from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FlagStatus(str, Enum):
    DISABLED = "disabled"
    TESTERS = "testers"
    PREMIUM = "premium"
    ALL = "all"
    CUSTOM = "custom"


class FlagRuleType(str, Enum):
    USER = "user"
    ROLE = "role"
    SEGMENT = "segment"
    PERCENTAGE = "percentage"


@dataclass(slots=True)
class FlagRule:
    type: FlagRuleType
    value: str
    rollout: int | None = None
    priority: int = 0
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        try:
            self.type = FlagRuleType(self.type)  # type: ignore[assignment]
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"invalid rule type: {self.type}") from exc
        self.value = str(self.value)
        if self.rollout is not None:
            self.rollout = int(self.rollout)


@dataclass(slots=True)
class FeatureFlag:
    slug: str
    status: FlagStatus = FlagStatus.DISABLED
    description: str | None = None
    rollout: int | None = None
    rules: tuple[FlagRule, ...] = field(default_factory=tuple)
    meta: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("flag slug is required")
        try:
            self.status = FlagStatus(self.status)  # type: ignore[assignment]
        except Exception as exc:
            raise ValueError(f"invalid flag status: {self.status}") from exc
        if self.rollout is not None:
            self.rollout = max(0, min(100, int(self.rollout)))
        if not isinstance(self.rules, tuple):
            self.rules = tuple(self.rules)
        if self.meta is not None:
            self.meta = dict(self.meta)

    @property
    def testers(self) -> tuple[str, ...]:
        return tuple(rule.value for rule in self.rules if rule.type is FlagRuleType.USER)

    @property
    def roles(self) -> tuple[str, ...]:
        values = [rule.value for rule in self.rules if rule.type is FlagRuleType.ROLE]
        if self.status is FlagStatus.PREMIUM and "premium" not in {v.lower() for v in values}:
            values.append("premium")
        return tuple(values)

    @property
    def segments(self) -> tuple[str, ...]:
        return tuple(rule.value for rule in self.rules if rule.type is FlagRuleType.SEGMENT)


@dataclass(slots=True)
class Flag:
    slug: str
    enabled: bool = True
    description: str | None = None
    rollout: int = 100
    users: set[str] = field(default_factory=set)
    roles: set[str] = field(default_factory=set)
    segments: set[str] = field(default_factory=set)
    meta: dict[str, Any] | None = None

    @property
    def testers(self) -> set[str]:
        return self.users

    @property
    def status(self) -> FlagStatus:
        if not self.enabled:
            return FlagStatus.DISABLED
        if any(role.lower() == "premium" for role in self.roles):
            return FlagStatus.PREMIUM
        if self.users:
            return FlagStatus.TESTERS
        if self.segments:
            return FlagStatus.CUSTOM
        if self.rollout not in (0, 100):
            return FlagStatus.CUSTOM
        return FlagStatus.ALL


__all__ = [
    "Flag",
    "FeatureFlag",
    "FlagRule",
    "FlagRuleType",
    "FlagStatus",
]
