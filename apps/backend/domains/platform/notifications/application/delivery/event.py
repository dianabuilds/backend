from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .utils import dedupe_emails, extract_email_values


@dataclass(slots=True)
class NotificationEvent:
    """Normalized notification payload used by delivery pipelines."""

    topic: str
    user_id: str
    title: str | None = None
    body: str | None = None
    type: str = "system"
    priority: str = "normal"
    cta_label: str | None = None
    cta_url: str | None = None
    meta: Mapping[str, Any] | None = None
    event_id: str | None = None
    context: Mapping[str, Any] | None = None
    is_preview: bool = False
    template_slug: str | None = None
    template_locale: str | None = None
    template_variables: Mapping[str, Any] | None = None
    email_to: tuple[str, ...] | None = None

    channel_key: str | None = field(default=None)

    @classmethod
    def from_payload(cls, topic: str, payload: Mapping[str, Any]) -> NotificationEvent:
        user_id = str(
            payload.get("user_id") or payload.get("recipient_id") or ""
        ).strip()
        if not user_id:
            raise ValueError("user_id_required")

        raw_title = str(payload.get("title") or "").strip() or None
        raw_body = (
            str(payload.get("body") or payload.get("message") or "").strip() or None
        )
        priority = str(payload.get("priority") or "normal").strip().lower() or "normal"
        type_ = str(payload.get("type") or "system").strip() or "system"

        cta_payload = payload.get("cta") or {}
        cta_label: str | None = None
        cta_url: str | None = None
        if isinstance(cta_payload, Mapping):
            label = cta_payload.get("label")
            url = cta_payload.get("url")
            if label:
                cta_label = str(label)
            if url:
                cta_url = str(url)

        meta = payload.get("meta") if isinstance(payload.get("meta"), Mapping) else None
        context = (
            payload.get("context")
            if isinstance(payload.get("context"), Mapping)
            else None
        )

        template_slug: str | None = None
        template_locale: str | None = None
        template_variables: Mapping[str, Any] | None = None
        template_payload = payload.get("template")
        if isinstance(template_payload, Mapping):
            template_slug = (
                str(
                    template_payload.get("slug")
                    or template_payload.get("id")
                    or template_payload.get("key")
                    or ""
                ).strip()
                or None
            )
            if template_payload.get("locale") is not None:
                locale_raw = str(template_payload.get("locale") or "").strip()
                template_locale = locale_raw or None
            candidate = template_payload.get("variables")
            if isinstance(candidate, Mapping):
                template_variables = dict(candidate)
        else:
            template_slug = (
                str(
                    payload.get("template_slug") or payload.get("template") or ""
                ).strip()
                or None
            )
            locale_value = payload.get("template_locale")
            if locale_value is not None:
                locale_raw = str(locale_value or "").strip()
                template_locale = locale_raw or None

        if template_variables is None:
            alt_variables = payload.get("template_variables") or payload.get(
                "variables"
            )
            if isinstance(alt_variables, Mapping):
                template_variables = dict(alt_variables)

        if (raw_title is None or raw_body is None) and not template_slug:
            raise ValueError("title_and_body_required")

        emails: list[str] = []
        for key in ("email_to", "emails", "email", "to"):
            emails.extend(extract_email_values(payload.get(key)))
        email_to_tuple = tuple(dedupe_emails(emails))
        email_to = email_to_tuple or None

        event_id = extract_event_id(topic, user_id, payload)
        channel_key = (
            str(payload.get("channel") or payload.get("channel_key") or "").strip()
            or None
        )

        return cls(
            topic=topic,
            user_id=user_id,
            title=raw_title,
            body=raw_body,
            type=type_,
            priority=priority,
            cta_label=cta_label,
            cta_url=cta_url,
            meta=meta,
            event_id=event_id,
            context=context,
            is_preview=bool(payload.get("is_preview", False)),
            template_slug=template_slug,
            template_locale=template_locale,
            template_variables=template_variables,
            email_to=email_to,
            channel_key=channel_key,
        )


def extract_event_id(
    topic: str, user_id: str, payload: Mapping[str, Any]
) -> str | None:
    for key in ("event_id", "dedupe_key", "resource_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)

    source = payload.get("meta")
    source_id = None
    if isinstance(source, Mapping):
        source_id = source.get("source_id") or source.get("id")

    template_payload = (
        payload.get("template")
        if isinstance(payload.get("template"), Mapping)
        else None
    )
    template_slug: str | None = None
    template_variables: Mapping[str, Any] | None = None
    if template_payload:
        template_slug = (
            template_payload.get("slug")
            or template_payload.get("id")
            or template_payload.get("key")
        )
        candidate = template_payload.get("variables")
        if isinstance(candidate, Mapping):
            template_variables = candidate

    if template_slug is None:
        template_slug = payload.get("template_slug") or payload.get("template")
    if template_variables is None:
        vars_candidate = payload.get("template_variables") or payload.get("variables")
        if isinstance(vars_candidate, Mapping):
            template_variables = vars_candidate

    base_parts = [
        topic,
        user_id,
        str(payload.get("title") or ""),
        str(payload.get("body") or payload.get("message") or ""),
    ]
    if template_slug:
        base_parts.append(str(template_slug))
    if isinstance(template_variables, Mapping):
        serialized: list[str] = []
        for key in sorted(str(k) for k in template_variables.keys()):
            try:
                value = template_variables[key]
            except KeyError:  # pragma: no cover - defensive
                value = template_variables.get(key)
            serialized.append(f"{key}={value!r}")
        if serialized:
            base_parts.append("|".join(serialized))
    if source_id:
        base_parts.append(str(source_id))
    base = "|".join(base_parts).strip()
    if len(base) < 3:
        return None
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


__all__ = ["NotificationEvent", "extract_event_id"]
