import datetime as dt

import pytest

from apps.backend.domains.platform.notifications.application import template_presenter
from apps.backend.domains.platform.notifications.application.template_use_cases import (
    delete_template,
    get_template,
    list_templates,
    upsert_template,
)
from apps.backend.domains.platform.notifications.domain.template import Template


class DummyTemplateService:
    def __init__(self, templates=None):
        self.templates = templates or []
        self.saved_payload = None
        self.deleted = None

    async def list(self, limit: int = 50, offset: int = 0):
        assert limit >= 0 and offset >= 0
        return list(self.templates)

    async def get(self, template_id: str):
        return next((t for t in self.templates if t.id == template_id), None)

    async def save(self, payload: dict):
        self.saved_payload = payload
        template = build_template(
            payload.get("id", "tmpl-1"), payload.get("slug", "slug-1")
        )
        self.templates.append(template)
        return template

    async def delete(self, template_id: str):
        self.deleted = template_id


def build_template(template_id="tmpl-1", slug="welcome") -> Template:
    now = dt.datetime(2025, 1, 1, tzinfo=dt.UTC)
    return Template(
        id=template_id,
        slug=slug,
        name="Welcome",
        description=None,
        subject="Hello",
        body="Hi there",
        locale="en",
        variables={"name": "John"},
        meta={"channel": "email"},
        created_by="system",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_list_templates_returns_serialized_items():
    service = DummyTemplateService([build_template()])
    result = await list_templates(service, limit=10, offset=0)
    assert result["items"][0]["slug"] == "welcome"
    assert result["items"][0]["variables"] == {"name": "John"}


@pytest.mark.asyncio
async def test_upsert_template_serializes_result():
    service = DummyTemplateService()
    result = await upsert_template(service, {"id": "tmpl-42", "slug": "info"})
    assert result["template"]["id"] == "tmpl-42"
    assert service.saved_payload["slug"] == "info"


@pytest.mark.asyncio
async def test_get_template_handles_missing():
    service = DummyTemplateService()
    assert await get_template(service, "missing") is None


@pytest.mark.asyncio
async def test_get_template_serializes_existing():
    template = build_template("tmpl-99", "promo")
    service = DummyTemplateService([template])
    result = await get_template(service, "tmpl-99")
    assert result["template"]["slug"] == "promo"


@pytest.mark.asyncio
async def test_delete_template_returns_ok():
    service = DummyTemplateService()
    result = await delete_template(service, "tmpl-1")
    assert result == {"ok": True}
    assert service.deleted == "tmpl-1"


def test_template_presenter_iso_format():
    template = build_template()
    payload = template_presenter.template_to_dict(template)
    assert payload["created_at"].endswith("Z")
    assert payload["updated_at"].endswith("Z")
