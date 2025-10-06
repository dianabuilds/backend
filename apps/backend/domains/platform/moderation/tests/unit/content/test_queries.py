from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ....application import content
from ....domain.dtos import ContentStatus, ContentType


@pytest.mark.asyncio
async def test_list_content_applies_filters(moderation_service, moderation_data):
    service = moderation_service
    target_id = moderation_data["content"]["pending"]

    result = await content.list_content(
        service,
        content_type=ContentType.node,
        status="pending",
        ai_label="spam",
        has_reports=True,
        author_id=moderation_data["users"]["alice"],
        limit=5,
    )

    assert [item.id for item in result["items"]] == [target_id]
    item = result["items"][0]
    assert item.complaints_count == 1
    assert item.meta["language"] == "en"
    assert result["next_cursor"] is None


@pytest.mark.asyncio
async def test_list_content_respects_date_range(moderation_service):
    service = moderation_service
    since = service._iso(service._now() - timedelta(hours=2))

    result = await content.list_content(
        service,
        has_reports=False,
        date_from=since,
        limit=10,
    )

    ids = {item.id for item in result["items"]}
    assert ids == {service.test_data["content"]["clean"]}  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_get_content_merges_reports(moderation_service, moderation_data):
    service = moderation_service
    summary = await content.get_content(service, moderation_data["content"]["pending"])

    assert summary.id == moderation_data["content"]["pending"]
    assert summary.reports and summary.reports[0].category == "spam"
    assert summary.moderation_history[0]["actor"] == "ai-moderator"


@pytest.mark.asyncio
async def test_get_content_missing_raises(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await content.get_content(service, "does-not-exist")


class DummyContentRepository:
    def __init__(self) -> None:
        self.queue_params: list[dict] = []

    async def list_queue(self, **params):
        self.queue_params.append(params)
        return {
            "items": [{"id": "db-item"}],
            "next_cursor": "cursor-1",
        }

    async def load_content_details(self, content_id: str):
        return {
            "author_id": "db-author",
            "created_at": "2025-01-07T12:00:00Z",
            "title": "from-db",
            "moderation_status": "hidden",
            "moderation_history": [{"action": "db"}],
            "node_status": "published",
            "moderation_status_updated_at": datetime(2025, 1, 7, tzinfo=UTC),
        }


@pytest.mark.asyncio
async def test_get_content_merges_repository_details(
    moderation_service, moderation_data
):
    service = moderation_service
    repo = DummyContentRepository()
    content_id = moderation_data["content"]["pending"]

    summary = await content.get_content(service, content_id, repository=repo)

    assert summary.author_id == "db-author"
    assert summary.status == ContentStatus.hidden
    assert summary.preview == "from-db"
    assert summary.moderation_history[0]["action"] == "db"
    assert summary.meta.get("node_status") == "published"


@pytest.mark.asyncio
async def test_list_queue_delegates_to_repository():
    repo = DummyContentRepository()

    result = await content.list_queue(repo, status="pending", limit=5, cursor="0")

    assert repo.queue_params[0]["status"] == "pending"
    assert result == {"items": [{"id": "db-item"}], "next_cursor": "cursor-1"}
