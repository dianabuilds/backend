from __future__ import annotations

import logging
from asyncio import TimeoutError as AsyncTimeoutError
from collections.abc import Mapping
from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.application.notify_service import NotifyService
from domains.platform.notifications.application.preference_service import (
    _default_opt_in,
)
from domains.platform.notifications.application.template_service import TemplateService
from domains.platform.notifications.logic.dispatcher import dispatch
from domains.platform.notifications.models.entities import (
    DeliveryRequirement,
    NotificationMatrix,
    PreferenceRecord,
    TopicChannelRule,
)
from domains.platform.notifications.ports import (
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
)

from .event import NotificationEvent
from .flags import DeliveryFlagEvaluator
from .utils import (
    ALLOWED_PRIORITIES,
    first_matching_preference,
    is_channel_available,
    normalize_topic,
    resolve_email_recipients,
)

logger = logging.getLogger(__name__)

_JINJA_ENV = Environment(
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

_DELIVERY_ERRORS = (
    RuntimeError,
    ValueError,
    ConnectionError,
    AsyncTimeoutError,
    OSError,
)


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
        topic_key = normalize_topic(event.topic, matrix)
        if topic_key is None:
            return None

        evaluator = DeliveryFlagEvaluator(
            self._flags, event.context or {"sub": event.user_id}
        )

        in_app_channel = matrix.channels.get("in_app")
        in_app_rule = matrix.get_rule(topic_key, "in_app")
        if not in_app_channel or not in_app_rule:
            return None
        if not await is_channel_available(evaluator, in_app_channel, in_app_rule):
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
            event.priority if event.priority in ALLOWED_PRIORITIES else "normal"
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
        evaluator: DeliveryFlagEvaluator,
    ) -> None:
        email_rule = matrix.get_rule(topic_key, "email")
        if email_rule is None:
            return
        email_channel = matrix.channels.get("email")
        if email_channel is None:
            return
        if not await is_channel_available(evaluator, email_channel, email_rule):
            return
        if not self._is_allowed_by_preferences(records, topic_key, "email", email_rule):
            return

        recipients = resolve_email_recipients(event)
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
        record = first_matching_preference(records, topic_key, channel_key)
        if record is None:
            return _default_opt_in(rule)
        return bool(record.opt_in)

    def _render_template(self, template: str, variables: Mapping[str, Any]) -> str:
        try:
            return _JINJA_ENV.from_string(template).render(**variables)
        except (TemplateError, TypeError, ValueError) as exc:
            raise ValueError("template_render_failed") from exc


__all__ = ["DeliveryService", "NotificationEvent"]
