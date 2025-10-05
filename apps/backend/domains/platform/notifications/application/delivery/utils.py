from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from domains.platform.notifications.models.entities import (
    NotificationChannel,
    NotificationMatrix,
    PreferenceRecord,
    TopicChannelRule,
)

ALLOWED_PRIORITIES = {"urgent", "high", "normal", "low"}

if TYPE_CHECKING:  # pragma: no cover
    from .event import NotificationEvent
    from .flags import DeliveryFlagEvaluator


def resolve_email_recipients(event: NotificationEvent) -> list[str]:
    candidates: list[str] = []
    if event.email_to:
        candidates.extend(event.email_to)
    for source in (event.meta, event.context):
        if isinstance(source, Mapping):
            for key in (
                "email_to",
                "emails",
                "email",
                "recipient_email",
                "recipient_emails",
                "to",
            ):
                candidates.extend(extract_email_values(source.get(key)))
    return dedupe_emails(candidates)


def extract_email_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return [item for item in parts if item]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            result.extend(extract_email_values(item))
        return result
    return []


def dedupe_emails(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        address = item.strip()
        if not address:
            continue
        lower = address.lower()
        if lower in seen:
            continue
        seen.add(lower)
        unique.append(address)
    return unique


def normalize_topic(topic: str, matrix: NotificationMatrix) -> str | None:
    key = topic.strip().lower()
    if ".v" in key:
        base, _, suffix = key.rpartition(".v")
        if suffix.isdigit():
            key = base
    if key in matrix.topics:
        return key
    aliases = {
        "content.engagement": "content.new_comment",
    }
    mapped = aliases.get(key)
    if mapped and mapped in matrix.topics:
        return mapped
    return None


async def is_channel_available(
    evaluator: DeliveryFlagEvaluator,
    channel: NotificationChannel,
    rule: TopicChannelRule,
) -> bool:
    if not channel.is_active:
        return False
    fallback = (
        rule.flag_fallback_enabled
        if rule.flag_fallback_enabled is not None
        else channel.flag_fallback_enabled
    )
    slug = rule.feature_flag or channel.feature_flag
    return await evaluator.is_enabled(slug, fallback=fallback)


def first_matching_preference(
    records: list[PreferenceRecord],
    topic_key: str,
    channel_key: str,
) -> PreferenceRecord | None:
    for record in records:
        if record.topic_key == topic_key and record.channel_key == channel_key:
            return record
    return None


__all__ = [
    "ALLOWED_PRIORITIES",
    "dedupe_emails",
    "extract_email_values",
    "first_matching_preference",
    "is_channel_available",
    "normalize_topic",
    "resolve_email_recipients",
]
