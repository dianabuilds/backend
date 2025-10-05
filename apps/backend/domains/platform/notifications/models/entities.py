from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DigestMode(str, Enum):
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"
    NONE = "none"


class DeliveryRequirement(str, Enum):
    MANDATORY = "mandatory"
    DEFAULT_ON = "default_on"
    OPT_IN = "opt_in"
    DISABLED = "disabled"


@dataclass(slots=True)
class NotificationChannel:
    key: str
    display_name: str
    category: str
    description: str | None = None
    feature_flag: str | None = None
    flag_fallback_enabled: bool = True
    supports_digest: bool = False
    requires_consent: bool = False
    is_active: bool = True
    position: int = 100
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NotificationTopic:
    key: str
    category: str
    display_name: str
    description: str | None = None
    default_digest: DigestMode = DigestMode.INSTANT
    default_quiet_hours: tuple[int, ...] = tuple()
    position: int = 100
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TopicChannelRule:
    topic_key: str
    channel_key: str
    delivery: DeliveryRequirement
    default_opt_in: bool | None = None
    default_digest: DigestMode | None = None
    feature_flag: str | None = None
    flag_fallback_enabled: bool | None = None
    position: int = 100
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PreferenceRecord:
    user_id: str
    topic_key: str
    channel_key: str
    opt_in: bool
    digest: str
    quiet_hours: tuple[int, ...] = tuple()
    consent_source: str = "user"
    consent_version: int = 1
    updated_by: str | None = None
    request_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ConsentAuditRecord:
    user_id: str
    topic_key: str
    channel_key: str
    previous_state: Mapping[str, Any] | None
    new_state: Mapping[str, Any]
    source: str
    changed_by: str | None
    request_id: str | None
    changed_at: datetime | None = None


@dataclass(slots=True)
class NotificationMatrix:
    topics: dict[str, NotificationTopic]
    channels: dict[str, NotificationChannel]
    rules: dict[tuple[str, str], TopicChannelRule]
    version: int = 1

    def topics_in_order(self) -> Sequence[NotificationTopic]:
        return tuple(
            sorted(self.topics.values(), key=lambda t: (int(t.position), t.key))
        )

    def channels_in_order(self) -> Sequence[NotificationChannel]:
        return tuple(
            sorted(self.channels.values(), key=lambda c: (int(c.position), c.key))
        )

    def topic_rules(self, topic_key: str) -> Sequence[TopicChannelRule]:
        items: Iterable[TopicChannelRule] = (
            rule for (t_key, _), rule in self.rules.items() if t_key == topic_key
        )
        return tuple(sorted(items, key=lambda r: (int(r.position), r.channel_key)))

    def get_rule(self, topic_key: str, channel_key: str) -> TopicChannelRule | None:
        return self.rules.get((topic_key, channel_key))


__all__ = [
    "DigestMode",
    "DeliveryRequirement",
    "NotificationChannel",
    "NotificationTopic",
    "TopicChannelRule",
    "PreferenceRecord",
    "ConsentAuditRecord",
    "NotificationMatrix",
]
