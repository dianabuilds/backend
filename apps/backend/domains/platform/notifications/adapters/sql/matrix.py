from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.models.entities import (
    DeliveryRequirement,
    DigestMode,
    NotificationChannel,
    NotificationMatrix,
    NotificationTopic,
    TopicChannelRule,
)
from domains.platform.notifications.ports import NotificationMatrixRepo

from .._engine import ensure_async_engine


class SQLNotificationMatrixRepo(NotificationMatrixRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = ensure_async_engine(engine)
        self._cache: NotificationMatrix | None = None

    async def load(self, *, use_cache: bool = True) -> NotificationMatrix:
        if use_cache and self._cache is not None:
            return self._cache
        async with self._engine.begin() as conn:
            channels_rows = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT
                            key,
                            display_name,
                            description,
                            category,
                            feature_flag_slug,
                            flag_fallback_enabled,
                            supports_digest,
                            requires_consent,
                            is_active,
                            position,
                            meta
                        FROM notification_channels
                        ORDER BY position, key
                        """
                        )
                    )
                )
                .mappings()
                .all()
            )
            topics_rows = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT
                            key,
                            category,
                            display_name,
                            description,
                            default_digest,
                            default_quiet_hours,
                            position,
                            meta
                        FROM notification_topics
                        ORDER BY position, key
                        """
                        )
                    )
                )
                .mappings()
                .all()
            )
            rules_rows = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT
                            topic_key,
                            channel_key,
                            delivery_requirement,
                            default_opt_in,
                            default_digest,
                            feature_flag_slug,
                            flag_fallback_enabled,
                            position,
                            meta
                        FROM notification_topic_channels
                        ORDER BY topic_key, position, channel_key
                        """
                        )
                    )
                )
                .mappings()
                .all()
            )

        channels = {
            str(row["key"]): NotificationChannel(
                key=str(row["key"]),
                display_name=str(row["display_name"]),
                category=str(row["category"]),
                description=(
                    str(row["description"]) if row.get("description") else None
                ),
                feature_flag=(
                    str(row["feature_flag_slug"])
                    if row.get("feature_flag_slug")
                    else None
                ),
                flag_fallback_enabled=bool(
                    row.get("flag_fallback_enabled")
                    if row.get("flag_fallback_enabled") is not None
                    else True
                ),
                supports_digest=bool(row.get("supports_digest")),
                requires_consent=bool(row.get("requires_consent")),
                is_active=bool(row.get("is_active", True)),
                position=int(row.get("position", 100)),
                meta=_ensure_dict(row.get("meta")),
            )
            for row in channels_rows
        }
        topics = {
            str(row["key"]): NotificationTopic(
                key=str(row["key"]),
                category=str(row["category"]),
                display_name=str(row["display_name"]),
                description=(
                    str(row["description"]) if row.get("description") else None
                ),
                default_digest=_coerce_digest(row.get("default_digest")),
                default_quiet_hours=_coerce_quiet_hours(row.get("default_quiet_hours")),
                position=int(row.get("position", 100)),
                meta=_ensure_dict(row.get("meta")),
            )
            for row in topics_rows
        }
        rules: dict[tuple[str, str], TopicChannelRule] = {}
        for row in rules_rows:
            topic_key = str(row["topic_key"])
            channel_key = str(row["channel_key"])
            rules[(topic_key, channel_key)] = TopicChannelRule(
                topic_key=topic_key,
                channel_key=channel_key,
                delivery=DeliveryRequirement(str(row["delivery_requirement"])),
                default_opt_in=(
                    bool(row["default_opt_in"])
                    if row.get("default_opt_in") is not None
                    else None
                ),
                default_digest=_coerce_digest(row.get("default_digest")),
                feature_flag=(
                    str(row["feature_flag_slug"])
                    if row.get("feature_flag_slug")
                    else None
                ),
                flag_fallback_enabled=(
                    bool(row.get("flag_fallback_enabled"))
                    if row.get("flag_fallback_enabled") is not None
                    else None
                ),
                position=int(row.get("position", 100)),
                meta=_ensure_dict(row.get("meta")),
            )
        allowed_channels = {"in_app", "email", "broadcasts"}
        channels = {
            key: value for key, value in channels.items() if key in allowed_channels
        }
        rules = {
            key: value for key, value in rules.items() if key[1] in allowed_channels
        }
        matrix = NotificationMatrix(topics=topics, channels=channels, rules=rules)
        self._cache = matrix
        return matrix

    def invalidate(self) -> None:
        self._cache = None


def _ensure_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _coerce_digest(value: Any) -> DigestMode:
    try:
        textual = str(value).strip().lower()
    except (AttributeError, ValueError):
        textual = DigestMode.INSTANT.value
    if textual not in {m.value for m in DigestMode}:
        textual = DigestMode.INSTANT.value
    return DigestMode(textual)


def _coerce_quiet_hours(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return tuple()
    hours: set[int] = set()
    for item in value:
        try:
            hour = int(item)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23:
            hours.add(hour)
    return tuple(sorted(hours))


__all__ = ["SQLNotificationMatrixRepo"]
