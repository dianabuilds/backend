from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.ports_notify import (
    INotificationRepository,
)

from ._engine import ensure_async_engine

_BASE_SELECT = """
SELECT
    r.id,
    r.user_id,
    m.title,
    m.message,
    m.type,
    r.placement,
    r.is_preview,
    r.created_at,
    r.read_at,
    m.topic_key,
    m.channel_key,
    r.priority,
    m.cta_label,
    m.cta_url,
    m.meta,
    r.event_id,
    r.updated_at
FROM notification_receipts r
JOIN notification_messages m ON m.id = r.message_id
"""

_MESSAGE_UPSERT = text(
    """
    INSERT INTO notification_messages (
        payload_hash,
        title,
        message,
        type,
        topic_key,
        channel_key,
        cta_label,
        cta_url,
        meta
    ) VALUES (
        :payload_hash,
        :title,
        :message,
        CAST(:type_value AS notificationtype),
        :topic_key,
        :channel_key,
        :cta_label,
        :cta_url,
        CAST(:meta AS jsonb)
    )
    ON CONFLICT (payload_hash) DO UPDATE SET
        title = EXCLUDED.title,
        message = EXCLUDED.message,
        type = EXCLUDED.type,
        topic_key = EXCLUDED.topic_key,
        channel_key = EXCLUDED.channel_key,
        cta_label = EXCLUDED.cta_label,
        cta_url = EXCLUDED.cta_url,
        meta = EXCLUDED.meta,
        updated_at = now()
    RETURNING id
    """
)

_RECEIPT_UPSERT = text(
    """
    INSERT INTO notification_receipts (
        user_id,
        message_id,
        placement,
        priority,
        is_preview,
        event_id
    ) VALUES (
        CAST(:user_id AS uuid),
        CAST(:message_id AS uuid),
        CAST(:placement AS notificationplacement),
        :priority,
        :is_preview,
        :event_id
    )
    ON CONFLICT (event_id) WHERE event_id IS NOT NULL DO UPDATE SET
        message_id = EXCLUDED.message_id,
        placement = EXCLUDED.placement,
        priority = EXCLUDED.priority,
        is_preview = EXCLUDED.is_preview,
        updated_at = now()
    RETURNING id,
              user_id,
              message_id
    """
)

_FETCH_BY_ID = text(_BASE_SELECT + "\nWHERE r.id = CAST(:id AS uuid)")
_FETCH_BY_EVENT = text(
    "SELECT id, user_id, message_id FROM notification_receipts WHERE event_id = :event_id"
)


class NotificationRepository(INotificationRepository):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine = ensure_async_engine(engine)

    async def create_and_commit(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        type_: str,
        placement: str,
        is_preview: bool = False,
        topic_key: str | None = None,
        channel_key: str | None = None,
        priority: str = "normal",
        cta_label: str | None = None,
        cta_url: str | None = None,
        meta: Mapping[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        if channel_key is None and placement == "inbox":
            channel_key = "in_app"

        topic_value = self._normalize_optional(topic_key)
        channel_value = self._normalize_optional(channel_key)
        cta_label_value = self._normalize_optional(cta_label)
        cta_url_value = self._normalize_optional(cta_url)
        title_value = str(title or "")
        message_value = str(message or "")
        type_raw = str(type_ or "")

        meta_payload = self._coerce_meta(meta)
        payload_hash = self._payload_hash(
            title=title_value,
            message=message_value,
            type_=self._normalize_type(type_raw),
            topic_key=topic_value,
            channel_key=channel_value,
            cta_label=cta_label_value,
            cta_url=cta_url_value,
            meta=meta_payload,
        )

        message_params = {
            "payload_hash": payload_hash,
            "title": title_value,
            "message": message_value,
            "type_value": self._normalize_type(type_raw),
            "topic_key": topic_value,
            "channel_key": channel_value,
            "cta_label": cta_label_value,
            "cta_url": cta_url_value,
            "meta": json.dumps(meta_payload, ensure_ascii=False),
        }

        normalized_priority = str(priority or "normal").strip() or "normal"

        async with self._engine.begin() as conn:
            message_result = await conn.execute(_MESSAGE_UPSERT, message_params)
            message_id = message_result.scalar()
            if message_id is None:
                lookup = await conn.execute(
                    text(
                        "SELECT id FROM notification_messages WHERE payload_hash = :payload_hash"
                    ),
                    {"payload_hash": payload_hash},
                )
                message_id = lookup.scalar()
            if message_id is None:
                raise RuntimeError("failed to persist notification message")

            receipt_params = {
                "user_id": user_id,
                "message_id": message_id,
                "placement": placement,
                "priority": normalized_priority,
                "is_preview": bool(is_preview),
                "event_id": event_id,
            }
            receipt_row = (
                (await conn.execute(_RECEIPT_UPSERT, receipt_params)).mappings().first()
            )
            if receipt_row is None and event_id:
                fallback = await conn.execute(_FETCH_BY_EVENT, {"event_id": event_id})
                receipt_row = fallback.mappings().first()
            if receipt_row is None:
                raise RuntimeError("failed to persist notification receipt")

            data = await conn.execute(_FETCH_BY_ID, {"id": receipt_row["id"]})
            row = data.mappings().first()
            if row is None:
                raise RuntimeError("failed to load notification")
            return self._normalize_row(row)

    async def list_for_user(
        self,
        user_id: str,
        *,
        placement: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        priority_expr = "COALESCE(r.priority, 'normal')"
        where_clauses = ["r.user_id = CAST(:uid AS uuid)"]
        params: dict[str, Any] = {
            "uid": user_id,
            "limit": int(limit),
            "offset": int(offset),
        }
        if placement:
            where_clauses.append(
                "r.placement = CAST(:placement AS notificationplacement)"
            )
            params["placement"] = placement
        sql = text(
            _BASE_SELECT
            + "\nWHERE "
            + " AND ".join(where_clauses)
            + f"\nORDER BY\n    CASE\n        WHEN {priority_expr} IN ('urgent', 'high') THEN 0\n        WHEN {priority_expr} = 'normal' THEN 1\n        ELSE 2\n    END,\n    r.created_at DESC\nLIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, params)).mappings().all()
        return [self._normalize_row(row) for row in rows]

    async def mark_read(self, user_id: str, notif_id: str) -> dict[str, Any] | None:
        sql = text(
            """
            WITH updated AS (
                UPDATE notification_receipts
                SET read_at = COALESCE(read_at, now()),
                    updated_at = now()
                WHERE id = CAST(:id AS uuid) AND user_id = CAST(:uid AS uuid) AND read_at IS NULL
                RETURNING id, message_id
            )
            SELECT
                r.id,
                r.user_id,
                m.title,
                m.message,
                m.type,
                r.placement,
                r.is_preview,
                r.created_at,
                r.read_at,
                m.topic_key,
                m.channel_key,
                r.priority,
                m.cta_label,
                m.cta_url,
                m.meta,
                r.event_id,
                r.updated_at
            FROM updated u
            JOIN notification_receipts r ON r.id = u.id
            JOIN notification_messages m ON m.id = u.message_id
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (await conn.execute(sql, {"id": notif_id, "uid": user_id}))
                .mappings()
                .first()
            )
        if not row:
            return None
        return self._normalize_row(row)

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        if value is None:
            return None
        text_value = str(value).strip()
        return text_value or None

    @staticmethod
    def _normalize_type(value: str | None) -> str:
        if not value:
            return "system"
        normalized = str(value).strip().lower()
        if normalized not in {"system", "user"}:
            return "system"
        return normalized

    @staticmethod
    def _coerce_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
        if meta is None:
            return {}
        if isinstance(meta, Mapping):
            return dict(meta)
        try:
            return dict(meta)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return {}

    @staticmethod
    def _payload_hash(
        *,
        title: str,
        message: str,
        type_: str,
        topic_key: str | None,
        channel_key: str | None,
        cta_label: str | None,
        cta_url: str | None,
        meta: dict[str, Any],
    ) -> str:
        meta_text = (
            json.dumps(meta, ensure_ascii=False, sort_keys=True) if meta else "{}"
        )
        parts = [
            title,
            message,
            type_,
            topic_key or "",
            channel_key or "",
            cta_label or "",
            cta_url or "",
            meta_text,
        ]
        joined = "|".join(parts)
        return hashlib.md5(joined.encode("utf-8")).hexdigest()

    def _normalize_row(self, row: Any) -> dict[str, Any]:
        data = dict(row)
        meta = data.get("meta")
        if isinstance(meta, str):
            try:
                data["meta"] = json.loads(meta) if meta else {}
            except json.JSONDecodeError:
                data["meta"] = {}
        elif isinstance(meta, Mapping):
            data["meta"] = dict(meta)
        else:
            data["meta"] = {}

        data["priority"] = str(data.get("priority") or "normal")
        data["is_preview"] = bool(data.get("is_preview"))
        if data.get("channel_key") is None and data.get("placement") == "inbox":
            data["channel_key"] = "in_app"
        if data.get("updated_at") is None:
            data["updated_at"] = data.get("read_at") or data.get("created_at")
        return data


__all__ = ["NotificationRepository"]
