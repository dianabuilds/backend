from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.models.entities import (
    ConsentAuditRecord,
    DeliveryRequirement,
    DigestMode,
    NotificationChannel,
    NotificationTopic,
    PreferenceRecord,
    TopicChannelRule,
)
from domains.platform.notifications.ports import (
    NotificationConsentAuditRepo,
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
)

_DIGEST_VALUES = {mode.value for mode in DigestMode}


logger = logging.getLogger(__name__)


@dataclass
class _FlagEvaluator:
    service: FlagService | None
    context: Mapping[str, Any]

    _cache: dict[str, bool]
    _known_slugs: set[str] | None

    def __init__(self, service: FlagService | None, context: Mapping[str, Any]):
        self.service = service
        self.context = dict(context or {})
        self._cache = {}
        self._known_slugs = None

    async def is_enabled(self, slug: str | None, *, fallback: bool = True) -> bool:
        if not slug:
            return True
        if self.service is None:
            return fallback
        if slug in self._cache:
            return self._cache[slug]
        try:
            enabled = bool(await self.service.evaluate(slug, dict(self.context)))
        except (RuntimeError, ValueError) as exc:
            logger.warning(
                "preference_flag_eval_failed", extra={"slug": slug}, exc_info=exc
            )
            self._cache[slug] = fallback
            return fallback
        if enabled:
            self._cache[slug] = True
            return True
        if self._known_slugs is None:
            try:
                flags = await self.service.list()
                self._known_slugs = {f.slug for f in flags}
            except (RuntimeError, ValueError) as exc:
                logger.warning("preference_flag_list_failed", exc_info=exc)
                self._known_slugs = set()
        if slug not in (self._known_slugs or set()):
            enabled = fallback
        self._cache[slug] = enabled
        return enabled


class PreferenceService:
    def __init__(
        self,
        *,
        matrix_repo: NotificationMatrixRepo,
        preference_repo: NotificationPreferenceRepo,
        audit_repo: NotificationConsentAuditRepo | None = None,
        flag_service: FlagService | None = None,
    ) -> None:
        self._matrix_repo = matrix_repo
        self._preference_repo = preference_repo
        self._audit_repo = audit_repo
        self._flags = flag_service

    async def get_preferences(
        self,
        user_id: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        matrix = await self._matrix_repo.load()
        stored = await self._preference_repo.list_for_user(user_id)
        stored_map = {
            (record.topic_key, record.channel_key): record for record in stored
        }
        version = max((record.consent_version for record in stored), default=0)

        evaluator = _FlagEvaluator(self._flags, context or {"sub": user_id})
        response: dict[str, Any] = {
            "__version": version,
            "__topics": _topics_meta(matrix.topics_in_order()),
            "__channels": _channels_meta(matrix.channels_in_order()),
        }

        for topic in matrix.topics_in_order():
            topic_payload: dict[str, Any] = {}
            for rule in matrix.topic_rules(topic.key):
                channel = matrix.channels.get(rule.channel_key)
                if not channel:
                    continue
                if not await _is_channel_available(evaluator, channel, rule):
                    continue
                record = stored_map.get((topic.key, channel.key))
                payload = _compose_preference_payload(topic, channel, rule, record)
                if payload is None:
                    continue
                topic_payload[channel.key] = payload
            if topic_payload:
                response[topic.key] = topic_payload
        return response

    async def get_preferences_overview(
        self,
        user_id: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        matrix = await self._matrix_repo.load()
        records = await self._preference_repo.list_for_user(user_id)
        evaluator = _FlagEvaluator(self._flags, context or {"sub": user_id})
        record_map = {
            (record.topic_key, record.channel_key): record for record in records
        }

        topics: list[dict[str, Any]] = []
        channels_acc: dict[str, dict[str, Any]] = {}
        email_digests: list[str] = []

        for topic in matrix.topics_in_order():
            topic_channels: list[dict[str, Any]] = []
            for rule in matrix.topic_rules(topic.key):
                channel = matrix.channels.get(rule.channel_key)
                if not channel:
                    continue
                if not await _is_channel_available(evaluator, channel, rule):
                    continue
                payload = _compose_preference_payload(
                    topic,
                    channel,
                    rule,
                    record_map.get((topic.key, channel.key)),
                )
                if payload is None:
                    continue
                channel_payload: dict[str, Any] = {
                    "key": channel.key,
                    "label": channel.display_name,
                    "opt_in": bool(payload["opt_in"]),
                    "delivery": payload["delivery"],
                    "locked": bool(payload["locked"]),
                }
                if payload.get("supports_digest"):
                    channel_payload["supports_digest"] = True
                    channel_payload["digest"] = payload["digest"]
                topic_channels.append(channel_payload)

                channel_summary = channels_acc.get(channel.key)
                if channel_summary is None:
                    channel_summary = {
                        "key": channel.key,
                        "label": channel.display_name,
                        "status": "optional",
                        "opt_in": False,
                        "order": int(channel.position),
                    }
                    channels_acc[channel.key] = channel_summary
                if rule.delivery is DeliveryRequirement.MANDATORY:
                    channel_summary["status"] = "required"
                elif (
                    rule.delivery is DeliveryRequirement.DEFAULT_ON
                    and channel_summary["status"] != "required"
                ):
                    channel_summary["status"] = "recommended"
                channel_summary["opt_in"] = channel_summary["opt_in"] or bool(
                    payload["opt_in"]
                )
                if channel.key == "email" and payload.get("supports_digest"):
                    email_digests.append(str(payload["digest"]))

            if topic_channels:
                topics.append(
                    {
                        "key": topic.key,
                        "label": topic.display_name,
                        "description": topic.description,
                        "channels": topic_channels,
                    }
                )

        channels = [
            {
                "key": entry["key"],
                "label": entry["label"],
                "status": entry["status"],
                "opt_in": entry["opt_in"],
            }
            for entry in sorted(channels_acc.values(), key=lambda item: item["order"])
        ]

        active_channels = sum(1 for entry in channels if entry["opt_in"])
        summary: dict[str, Any] = {
            "active_channels": active_channels,
            "total_channels": len(channels),
        }
        if email_digests:
            digest_value = Counter(email_digests).most_common(1)[0][0]
            summary["email_digest"] = digest_value

        timestamps = [
            ts
            for record in records
            for ts in (record.updated_at, record.created_at)
            if ts is not None
        ]
        if timestamps:
            summary["updated_at"] = max(timestamps).isoformat()

        return {
            "channels": channels,
            "topics": topics,
            "summary": summary,
        }

    async def set_preferences(
        self,
        user_id: str,
        prefs: Mapping[str, Any],
        *,
        actor_id: str | None = None,
        source: str = "user",
        context: Mapping[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        matrix = await self._matrix_repo.load()
        stored = await self._preference_repo.list_for_user(user_id)
        stored_map = {
            (record.topic_key, record.channel_key): record for record in stored
        }
        evaluator = _FlagEvaluator(self._flags, context or {"sub": user_id})
        next_version = max((record.consent_version for record in stored), default=0) + 1

        incoming = prefs if isinstance(prefs, Mapping) else {}
        updated_records: list[PreferenceRecord] = []
        audit_entries: list[ConsentAuditRecord] = []

        for topic in matrix.topics_in_order():
            topic_changes = incoming.get(topic.key)
            for rule in matrix.topic_rules(topic.key):
                channel = matrix.channels.get(rule.channel_key)
                if not channel:
                    continue
                if not await _is_channel_available(evaluator, channel, rule):
                    continue
                previous = stored_map.get((topic.key, channel.key))
                channel_incoming = None
                if isinstance(topic_changes, Mapping):
                    channel_incoming = topic_changes.get(channel.key)
                record = _build_preference_record(
                    user_id,
                    topic=topic,
                    channel=channel,
                    rule=rule,
                    incoming=channel_incoming,
                    previous=previous,
                    version=next_version,
                    source=source,
                    actor_id=actor_id,
                    request_id=request_id,
                )
                updated_records.append(record)
                if _preference_changed(previous, record):
                    audit_entries.append(
                        ConsentAuditRecord(
                            user_id=user_id,
                            topic_key=topic.key,
                            channel_key=channel.key,
                            previous_state=_state_from_record(previous),
                            new_state=_state_from_record(record) or {},
                            source=source,
                            changed_by=actor_id,
                            request_id=request_id,
                        )
                    )

        await self._preference_repo.replace_for_user(user_id, updated_records)
        if audit_entries and self._audit_repo is not None:
            await self._audit_repo.append_many(audit_entries)


def _topics_meta(topics: Sequence[NotificationTopic]) -> dict[str, Any]:
    return {
        topic.key: {
            "category": topic.category,
            "display_name": topic.display_name,
            "description": topic.description,
            "position": topic.position,
        }
        for topic in topics
    }


def _channels_meta(channels: Sequence[NotificationChannel]) -> dict[str, Any]:
    return {
        channel.key: {
            "category": channel.category,
            "display_name": channel.display_name,
            "description": channel.description,
            "supports_digest": channel.supports_digest,
            "requires_consent": channel.requires_consent,
            "feature_flag": channel.feature_flag,
            "position": channel.position,
        }
        for channel in channels
    }


async def _is_channel_available(
    evaluator: _FlagEvaluator,
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


def _compose_preference_payload(
    topic: NotificationTopic,
    channel: NotificationChannel,
    rule: TopicChannelRule,
    record: PreferenceRecord | None,
) -> dict[str, Any] | None:
    if rule.delivery is DeliveryRequirement.DISABLED:
        return None
    locked = rule.delivery is DeliveryRequirement.MANDATORY
    default_opt_in = _default_opt_in(rule)
    opt_in = bool(record.opt_in) if record is not None else default_opt_in
    if locked:
        opt_in = True
    digest = _resolve_digest_value(topic, channel, rule, record)
    quiet_hours = (
        list(record.quiet_hours)
        if record is not None
        else list(topic.default_quiet_hours)
    )
    return {
        "opt_in": opt_in,
        "digest": digest,
        "quiet_hours": quiet_hours,
        "locked": locked,
        "delivery": rule.delivery.value,
        "supports_digest": channel.supports_digest,
        "requires_consent": channel.requires_consent,
    }


def _build_preference_record(
    user_id: str,
    *,
    topic: NotificationTopic,
    channel: NotificationChannel,
    rule: TopicChannelRule,
    incoming: Any,
    previous: PreferenceRecord | None,
    version: int,
    source: str,
    actor_id: str | None,
    request_id: str | None,
) -> PreferenceRecord:
    incoming_opt_in, incoming_digest, incoming_quiet_hours = _parse_incoming(incoming)
    locked = rule.delivery is DeliveryRequirement.MANDATORY
    opt_in = _default_opt_in(rule)
    if previous is not None:
        opt_in = bool(previous.opt_in)
    if incoming_opt_in is not None:
        opt_in = bool(incoming_opt_in)
    if locked:
        opt_in = True

    digest = _resolve_digest_value(topic, channel, rule, previous)
    if incoming_digest is not None:
        digest = _normalize_digest(incoming_digest, channel, rule, topic)

    quiet_hours = tuple(topic.default_quiet_hours)
    if previous is not None:
        quiet_hours = previous.quiet_hours
    if incoming_quiet_hours is not None:
        quiet_hours = incoming_quiet_hours

    if not channel.supports_digest:
        digest = DigestMode.INSTANT.value
    now = datetime.now(tz=UTC)
    created_at = (
        now if previous is None or previous.created_at is None else previous.created_at
    )
    return PreferenceRecord(
        user_id=user_id,
        topic_key=topic.key,
        channel_key=channel.key,
        opt_in=opt_in,
        digest=digest,
        quiet_hours=quiet_hours,
        consent_source=source,
        consent_version=version,
        updated_by=actor_id,
        request_id=request_id,
        created_at=created_at,
        updated_at=now,
    )


def _parse_incoming(
    incoming: Any,
) -> tuple[bool | None, str | None, tuple[int, ...] | None]:
    if isinstance(incoming, Mapping):
        opt_in = (
            incoming.get("opt_in") if isinstance(incoming.get("opt_in"), bool) else None
        )
        digest = (
            incoming.get("digest") if isinstance(incoming.get("digest"), str) else None
        )
        quiet_hours = _normalize_quiet_hours(incoming.get("quiet_hours"))
        return opt_in, digest, quiet_hours
    if isinstance(incoming, bool):
        return bool(incoming), None, None
    return None, None, None


def _normalize_quiet_hours(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        return None
    bucket: set[int] = set()
    for item in value:
        try:
            hour = int(item)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23:
            bucket.add(hour)
    return tuple(sorted(bucket))


def _resolve_digest_value(
    topic: NotificationTopic,
    channel: NotificationChannel,
    rule: TopicChannelRule,
    record: PreferenceRecord | None,
) -> str:
    if record is not None and record.digest in _DIGEST_VALUES:
        return record.digest
    default_digest = (
        rule.default_digest.value if rule.default_digest else topic.default_digest.value
    )
    if not channel.supports_digest:
        return DigestMode.INSTANT.value
    return (
        default_digest if default_digest in _DIGEST_VALUES else DigestMode.INSTANT.value
    )


def _normalize_digest(
    digest: str,
    channel: NotificationChannel,
    rule: TopicChannelRule,
    topic: NotificationTopic,
) -> str:
    value = str(digest).strip().lower()
    if value not in _DIGEST_VALUES:
        return _resolve_digest_value(topic, channel, rule, None)
    if not channel.supports_digest:
        return DigestMode.INSTANT.value
    return value


def _default_opt_in(rule: TopicChannelRule) -> bool:
    if rule.default_opt_in is not None:
        return bool(rule.default_opt_in)
    if rule.delivery is DeliveryRequirement.MANDATORY:
        return True
    if rule.delivery is DeliveryRequirement.DEFAULT_ON:
        return True
    if rule.delivery is DeliveryRequirement.OPT_IN:
        return False
    return False


def _preference_changed(
    previous: PreferenceRecord | None, current: PreferenceRecord
) -> bool:
    if previous is None:
        return True
    if previous.opt_in != current.opt_in:
        return True
    if previous.digest != current.digest:
        return True
    if tuple(previous.quiet_hours) != tuple(current.quiet_hours):
        return True
    return False


def _state_from_record(record: PreferenceRecord | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "opt_in": bool(record.opt_in),
        "digest": record.digest,
        "quiet_hours": list(record.quiet_hours),
    }


__all__ = ["PreferenceService"]
