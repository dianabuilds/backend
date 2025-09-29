from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.application.delivery_service import (
    DeliveryService,
    NotificationEvent,
)
from domains.platform.notifications.application.notify_service import NotifyService
from domains.platform.notifications.application.template_service import TemplateService
from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.models.entities import (
    DeliveryRequirement,
    NotificationChannel,
    NotificationMatrix,
    NotificationTopic,
    PreferenceRecord,
    TopicChannelRule,
)


class InMemoryTemplateRepo:
    def __init__(self) -> None:
        self._items: dict[str, Template] = {}

    async def list(self, limit: int = 50, offset: int = 0) -> list[Template]:
        return list(self._items.values())[offset : offset + limit]

    async def get(self, template_id: str) -> Template | None:
        return self._items.get(template_id)

    async def get_by_slug(self, slug: str) -> Template | None:
        for item in self._items.values():
            if item.slug == slug:
                return item
        return None

    async def upsert(self, payload: dict[str, Any]) -> Template:
        template_id = str(payload.get("id") or uuid4())
        created = payload.get("created_at")
        created_at = created if isinstance(created, datetime) else datetime.now(UTC)
        variables = payload.get("variables")
        meta = payload.get("meta")
        template = Template(
            id=template_id,
            slug=str(payload["slug"]),
            name=str(payload["name"]),
            description=payload.get("description"),
            subject=payload.get("subject"),
            body=str(payload["body"]),
            locale=payload.get("locale"),
            variables=dict(variables) if isinstance(variables, dict) else None,
            meta=dict(meta) if isinstance(meta, dict) else None,
            created_by=payload.get("created_by"),
            created_at=created_at,
            updated_at=datetime.now(UTC),
        )
        self._items[template_id] = template
        return template

    async def delete(self, template_id: str) -> None:
        self._items.pop(template_id, None)


@pytest.mark.asyncio
async def test_template_service_generates_unique_slug_and_normalizes_locale() -> None:
    repo = InMemoryTemplateRepo()
    svc = TemplateService(repo)

    first = await svc.save({"name": "Payment Success", "body": "Body", "locale": "EN"})
    assert first.slug == "payment-success"
    assert first.locale == "en"

    second = await svc.save({"name": "Payment Success", "body": "Another body"})
    assert second.slug == "payment-success-2"
    assert second.id != first.id

    stored = await repo.get_by_slug("payment-success")
    assert stored is first

    with pytest.raises(ValueError):
        await svc.save({"name": "Test", "body": "Body", "locale": "fr"})


class StubMatrixRepo:
    def __init__(self, matrix: NotificationMatrix) -> None:
        self._matrix = matrix

    async def load(self, *, use_cache: bool = True) -> NotificationMatrix:
        return self._matrix


class StubPreferenceRepo:
    async def list_for_user(self, user_id: str) -> list[PreferenceRecord]:
        return []

    async def replace_for_user(self, user_id: str, records: Sequence[PreferenceRecord]) -> None:
        return None


class StubFlagService:
    async def evaluate(self, slug: str, context: dict[str, Any]) -> bool:
        return True


class StubNotifyService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create_notification(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(dict(kwargs))
        result = dict(kwargs)
        result["id"] = str(uuid4())
        return result


class StubTemplateService:
    def __init__(self, template: Template) -> None:
        self.template = template

    async def get_by_slug(self, slug: str) -> Template | None:
        if slug == self.template.slug:
            return self.template
        return None


@pytest.mark.asyncio
async def test_template_service_accepts_json_strings() -> None:
    repo = InMemoryTemplateRepo()
    svc = TemplateService(repo)

    tmpl = await svc.save({"name": "Payment", "body": "Body", "variables": '{"flag": true}'})
    assert tmpl.variables == {"flag": True}

    with pytest.raises(ValueError):
        await svc.save({"name": "Bad", "body": "Body", "variables": "not json"})


@pytest.mark.asyncio
async def test_delivery_service_renders_template_with_variables() -> None:
    topic_key = "economy.billing"
    matrix = NotificationMatrix(
        topics={
            topic_key: NotificationTopic(key=topic_key, category="billing", display_name="Billing")
        },
        channels={
            "in_app": NotificationChannel(
                key="in_app",
                display_name="In-App",
                category="system",
            )
        },
        rules={
            (topic_key, "in_app"): TopicChannelRule(
                topic_key=topic_key,
                channel_key="in_app",
                delivery=DeliveryRequirement.MANDATORY,
            )
        },
    )
    notify = StubNotifyService()
    template = Template(
        id="tmpl-1",
        slug="payment-success",
        name="Payment Success",
        description=None,
        subject="Привет, {{username}}!",
        body="Твой платёж был совершён успешно!",
        locale="ru",
        variables={"username": "друг"},
        meta=None,
        created_by="tester",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    template_service = StubTemplateService(template)
    service = DeliveryService(
        matrix_repo=StubMatrixRepo(matrix),
        preference_repo=StubPreferenceRepo(),
        notify_service=cast(NotifyService, notify),
        template_service=cast(TemplateService, template_service),
        flag_service=cast(FlagService, StubFlagService()),
    )

    payload = {
        "user_id": "user-123",
        "template": {"slug": "payment-success"},
        "template_variables": {"username": "sunny"},
        "priority": "high",
        "meta": {"source_id": "payment-1"},
    }
    event = NotificationEvent.from_payload(topic_key, payload)

    result = await service.deliver_to_inbox(event)
    assert result is not None

    assert notify.calls, "notification should be sent"
    call = notify.calls[0]
    assert call["title"] == "Привет, sunny!"
    assert call["message"] == "Твой платёж был совершён успешно!"
    assert call["meta"]["topic"] == topic_key
    assert call["meta"]["priority"] == "high"
    assert call["user_id"] == "user-123"
