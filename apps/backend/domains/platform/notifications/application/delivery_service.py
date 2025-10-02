from __future__ import annotations

import hashlib
import logging
from asyncio import TimeoutError as AsyncTimeoutError
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.application.notify_service import (
    NotifyService,
)
from domains.platform.notifications.application.preference_service import (
    _default_opt_in,  # type: ignore
)
from domains.platform.notifications.application.template_service import (
    TemplateService,
)
from domains.platform.notifications.logic.dispatcher import dispatch
from domains.platform.notifications.models.entities import (
    DeliveryRequirement,
    NotificationChannel,
    NotificationMatrix,
    PreferenceRecord,
    TopicChannelRule,
)
from domains.platform.notifications.ports import (
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
)

_ALLOWED_PRIORITIES = {"urgent", "high", "normal", "low"}
_JINJA_ENV = Environment(
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)
_DELIVERY_ERRORS = (
    RuntimeError,
    ValueError,
    ConnectionError,
    AsyncTimeoutError,
    OSError,
)


@dataclass(slots=True)
class NotificationEvent:
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
        cta = payload.get("cta") or {}
        cta_label = None
        cta_url = None
        if isinstance(cta, Mapping):
            if cta.get("label"):
                cta_label = str(cta.get("label"))
            if cta.get("url"):
                cta_url = str(cta.get("url"))
        meta = payload.get("meta") if isinstance(payload.get("meta"), Mapping) else None
        context = (
            payload.get("context")
            if isinstance(payload.get("context"), Mapping)
            else None
        )

        template_slug = None
        template_locale = None
        template_variables: Mapping[str, Any] | None = None
        template_data = payload.get("template")
        if isinstance(template_data, Mapping):
            template_slug = (
                str(
                    template_data.get("slug")
                    or template_data.get("id")
                    or template_data.get("key")
                    or ""
                ).strip()
                or None
            )
            if template_data.get("locale") is not None:
                locale_raw = str(template_data.get("locale") or "").strip()
                template_locale = locale_raw or None
            vars_candidate = template_data.get("variables")
            if isinstance(vars_candidate, Mapping):
                template_variables = dict(vars_candidate)
        else:
            template_slug = (
                str(
                    payload.get("template_slug") or payload.get("template") or ""
                ).strip()
                or None
            )
            locale_value = payload.get("template_locale")
            if locale_value is not None:
                locale_str = str(locale_value or "").strip()
                template_locale = locale_str or None

        if template_variables is None:
            alt_variables = payload.get("template_variables") or payload.get(
                "variables"
            )
            if isinstance(alt_variables, Mapping):
                template_variables = dict(alt_variables)

        if (raw_title is None or raw_body is None) and not template_slug:
            raise ValueError("title_and_body_required")

        email_candidates: list[str] = []
        for key in ("email_to", "emails", "email", "to"):
            email_candidates.extend(_extract_email_list(payload.get(key)))
        email_to = tuple(dict.fromkeys(email_candidates)) or None

        event_id = _extract_event_id(topic, user_id, payload)
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


def _extract_event_id(
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
    template = (
        payload.get("template")
        if isinstance(payload.get("template"), Mapping)
        else None
    )
    template_slug: str | None = None
    template_vars: Mapping[str, Any] | None = None
    if template:
        template_slug = (
            template.get("slug") or template.get("id") or template.get("key")
        )
        vars_candidate = template.get("variables")
        if isinstance(vars_candidate, Mapping):
            template_vars = vars_candidate
    if template_slug is None:
        template_slug = payload.get("template_slug") or payload.get("template")
    if template_vars is None:
        vars_candidate = payload.get("template_variables") or payload.get("variables")
        if isinstance(vars_candidate, Mapping):
            template_vars = vars_candidate
    base_parts = [
        topic,
        user_id,
        str(payload.get("title") or ""),
        str(payload.get("body") or payload.get("message") or ""),
    ]
    if template_slug:
        base_parts.append(str(template_slug))
    if isinstance(template_vars, Mapping):
        serialized: list[str] = []
        for key in sorted(str(k) for k in template_vars.keys()):
            try:
                value = template_vars[key]
            except KeyError:  # pragma: no cover - defensive
                value = template_vars.get(key)
            serialized.append(f"{key}={value!r}")
        if serialized:
            base_parts.append("|".join(serialized))
    if source_id:
        base_parts.append(str(source_id))
    base = "|".join(base_parts).strip()
    if not base or len(base) < 3:
        return None
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class DeliveryService:
    def __init__(
        self,
        matrix_repo: NotificationMatrixRepo,
        preference_repo: NotificationPreferenceRepo,
        notify_service: NotifyService,
        template_service: TemplateService | None = None,
        flag_service: FlagService | None = None,
    ) -> None:
        self._matrix_repo = matrix_repo
        self._preference_repo = preference_repo
        self._notify = notify_service
        self._templates = template_service
        self._flags = flag_service

    async def deliver_to_inbox(self, event: NotificationEvent) -> dict[str, Any] | None:
        matrix = await self._matrix_repo.load()
        topic_key = _normalize_topic(event.topic, matrix)
        if topic_key is None:
            return None

        evaluator = _FlagEvaluator(self._flags, event.context or {"sub": event.user_id})

        in_app_channel = matrix.channels.get("in_app")
        in_app_rule = matrix.get_rule(topic_key, "in_app")
        if not in_app_channel or not in_app_rule:
            return None
        if not await _is_channel_available(evaluator, in_app_channel, in_app_rule):
            return None

        records = await self._preference_repo.list_for_user(event.user_id)
        if not self._is_allowed_by_preferences(
            records, topic_key, "in_app", in_app_rule
        ):
            return None

        materialized = await self._materialize_event_content(event)
        if materialized is None:
            return None
        title, body = materialized

        payload_meta = dict(event.meta or {})
        payload_meta.setdefault("topic", topic_key)
        sanitized_priority = (
            event.priority if event.priority in _ALLOWED_PRIORITIES else "normal"
        )
        payload_meta.setdefault("priority", sanitized_priority)

        dto = await self._notify.create_notification(
            user_id=event.user_id,
            title=title,
            message=body,
            type_=event.type,
            placement="inbox",
            is_preview=event.is_preview,
            topic_key=topic_key,
            channel_key=event.channel_key or "in_app",
            priority=sanitized_priority,
            cta_label=event.cta_label,
            cta_url=event.cta_url,
            meta=payload_meta,
            event_id=event.event_id,
        )

        await self._maybe_send_email(
            event=event,
            topic_key=topic_key,
            title=title,
            body=body,
            records=records,
            matrix=matrix,
            evaluator=evaluator,
        )
        return dto

    async def _maybe_send_email(
        self,
        *,
        event: NotificationEvent,
        topic_key: str,
        title: str,
        body: str,
        records: list[PreferenceRecord],
        matrix: NotificationMatrix,
        evaluator: _FlagEvaluator,
    ) -> None:
        email_rule = matrix.get_rule(topic_key, "email")
        if email_rule is None:
            return
        email_channel = matrix.channels.get("email")
        if email_channel is None:
            return
        if not await _is_channel_available(evaluator, email_channel, email_rule):
            return
        if not self._is_allowed_by_preferences(records, topic_key, "email", email_rule):
            return

        recipients = _resolve_email_recipients(event)
        if not recipients:
            return

        payload = {
            "to": recipients,
            "subject": title,
            "text": body,
        }
        if isinstance(event.meta, Mapping):
            html = event.meta.get("email_html")
            if isinstance(html, str) and html.strip():
                payload["html"] = html
        try:
            dispatch("email", payload)
        except _DELIVERY_ERRORS as exc:
            logger.warning(
                "notification_email_dispatch_failed",
                extra={"recipients": recipients},
                exc_info=exc,
            )

    async def _materialize_event_content(
        self, event: NotificationEvent
    ) -> tuple[str, str] | None:
        title = event.title or ""
        body = event.body or ""
        if event.template_slug and self._templates is not None:
            template = await self._templates.get_by_slug(event.template_slug)
            if template is None:
                return None
            if (
                event.template_locale
                and template.locale
                and template.locale != event.template_locale
            ):
                return None
            variables: dict[str, Any] = {}
            if isinstance(template.variables, Mapping):
                variables.update(template.variables)
            if isinstance(event.context, Mapping):
                for key, value in event.context.items():
                    if isinstance(key, str) and key:
                        variables.setdefault(key, value)
            if isinstance(event.template_variables, Mapping):
                variables.update(event.template_variables)
            try:
                body_source = body or template.body
                if not body_source:
                    return None
                body = self._render_template(body_source, variables)
                title_source = title or template.subject or template.name or ""
                title = (
                    self._render_template(title_source, variables)
                    if title_source
                    else ""
                )
            except ValueError:
                return None
        if not title:
            return None
        if not body:
            return None
        return str(title), str(body)

    def _is_allowed_by_preferences(
        self,
        records: list[PreferenceRecord],
        topic_key: str,
        channel_key: str,
        rule: TopicChannelRule,
    ) -> bool:
        if rule.delivery is DeliveryRequirement.MANDATORY:
            return True
        record = _first_matching_preference(records, topic_key, channel_key)
        if record is None:
            return _default_opt_in(rule)
        return bool(record.opt_in)

    def _render_template(self, template: str, variables: Mapping[str, Any]) -> str:
        try:
            return _JINJA_ENV.from_string(template).render(**variables)
        except (TemplateError, TypeError, ValueError) as exc:
            raise ValueError("template_render_failed") from exc


class _FlagEvaluator:
    def __init__(self, service: FlagService | None, context: Mapping[str, Any]) -> None:
        self._service = service
        self._context = dict(context or {})
        self._cache: dict[str, bool] = {}

    async def is_enabled(self, slug: str | None, *, fallback: bool = True) -> bool:
        if not slug:
            return True
        if self._service is None:
            return fallback
        if slug in self._cache:
            return self._cache[slug]
        try:
            flag = await self._service.store.get(slug)
        except (RuntimeError, ValueError) as exc:
            logger.warning(
                "delivery_flag_fetch_failed", extra={"slug": slug}, exc_info=exc
            )
            enabled = fallback
        else:
            if flag is None:
                enabled = fallback
            else:
                enabled = bool(self._service._eval_flag(flag, dict(self._context)))
        self._cache[slug] = enabled
        return enabled


def _resolve_email_recipients(event: NotificationEvent) -> list[str]:
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
                candidates.extend(_extract_email_list(source.get(key)))
    seen: set[str] = set()
    unique: list[str] = []
    for item in candidates:
        normalized = str(item).strip()
        if not normalized:
            continue
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def _extract_email_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidate = value.strip()
        return [candidate] if candidate else []
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            result.extend(_extract_email_list(item))
        return result
    return []


def _normalize_topic(topic: str, matrix: NotificationMatrix) -> str | None:
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


def _first_matching_preference(
    records: list[PreferenceRecord],
    topic_key: str,
    channel_key: str,
) -> PreferenceRecord | None:
    for record in records:
        if record.topic_key == topic_key and record.channel_key == channel_key:
            return record
    return None


__all__ = ["DeliveryService", "NotificationEvent"]
