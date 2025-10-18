from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)
from domains.platform.notifications.application.messages_presenter import (
    build_list_response,
    notification_to_dict,
)
from domains.platform.notifications.application.messages_use_cases import (
    list_notifications,
    mark_notification_read,
    send_notification,
)


class StubUser:
    def __init__(self, user_id: str) -> None:
        self.id = user_id


class StubUsersService:
    def __init__(self, user: StubUser | None) -> None:
        self._user = user
        self.calls: list[str] = []

    async def get(self, identifier: str) -> StubUser | None:
        self.calls.append(identifier)
        return self._user


class StubRepo:
    def __init__(self) -> None:
        self.list_calls: list[dict[str, Any]] = []
        self.read_calls: list[tuple[str, str]] = []
        self.rows: list[dict[str, Any]] = []
        self.read_result: dict[str, Any] | None = None

    async def list_for_user(
        self,
        user_id: str,
        *,
        placement: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self.list_calls.append(
            {
                "user_id": user_id,
                "placement": placement,
                "limit": limit,
                "offset": offset,
            }
        )
        return list(self.rows)

    async def mark_read(self, user_id: str, notif_id: str) -> dict[str, Any] | None:
        self.read_calls.append((user_id, notif_id))
        return self.read_result


class StubNotify:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.result = {
            "id": "n-1",
            "user_id": "user-1",
            "priority": "normal",
            "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        }

    async def create_notification(self, command: Any) -> dict[str, Any]:
        self.calls.append(command)
        return dict(self.result)


def test_notification_to_dict_formats_fields() -> None:
    row = {
        "id": "n-1",
        "created_at": datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        "updated_at": datetime(2025, 1, 1, 12, 5, tzinfo=UTC),
        "read_at": None,
        "meta": '{"foo": 1}',
        "priority": None,
    }
    data = notification_to_dict(row)
    assert data["created_at"] == "2025-01-01T12:00:00+00:00"
    assert data["meta"] == {"foo": 1}
    assert data["priority"] == "normal"
    assert data["is_read"] is False


def test_build_list_response_counts_unread() -> None:
    items = [
        {"id": "1", "is_read": False},
        {"id": "2", "is_read": True},
    ]
    payload = build_list_response(items)
    assert payload["unread"] == 1


@pytest.mark.asyncio
async def test_list_notifications_resolves_user_and_returns_payload() -> None:
    repo = StubRepo()
    repo.rows = [
        {
            "id": "n-1",
            "created_at": datetime(2025, 1, 1, tzinfo=UTC),
            "meta": {},
            "read_at": None,
            "priority": "normal",
        }
    ]
    users = StubUsersService(StubUser("user-123"))

    result = await list_notifications(
        repo,
        users,
        subject="external-id",
        limit=25,
        offset=5,
    )

    assert repo.list_calls[0]["user_id"] == "user-123"
    assert result["items"][0]["id"] == "n-1"
    assert result["unread"] == 1


@pytest.mark.asyncio
async def test_list_notifications_generates_uuid_for_unknown_user() -> None:
    repo = StubRepo()
    repo.rows = []
    users = StubUsersService(None)

    await list_notifications(repo, users, subject="test@example.com")

    generated_id = repo.list_calls[0]["user_id"]
    expected = uuid.uuid5(uuid.NAMESPACE_DNS, "user:test@example.com")
    assert generated_id == str(expected)


@pytest.mark.asyncio
async def test_mark_notification_read_returns_payload() -> None:
    repo = StubRepo()
    repo.read_result = {
        "id": "n-1",
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        "meta": {},
        "read_at": datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    }
    users = StubUsersService(StubUser("user-123"))

    result = await mark_notification_read(
        repo,
        users,
        subject="user-123",
        notification_id="n-1",
    )

    assert result["notification"]["id"] == "n-1"
    assert repo.read_calls == [("user-123", "n-1")]


@pytest.mark.asyncio
async def test_mark_notification_read_handles_missing() -> None:
    repo = StubRepo()
    users = StubUsersService(StubUser("user-123"))
    with pytest.raises(NotificationError) as exc:
        await mark_notification_read(
            repo,
            users,
            subject="user-123",
            notification_id="missing",
        )
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_send_notification_parses_string_meta() -> None:
    service = StubNotify()
    payload = {
        "user_id": "user-1",
        "title": "Hello",
        "message": "Welcome",
        "meta": '{"foo": 1}',
    }

    result = await send_notification(service, payload)

    assert service.calls[0]["meta"] == {"foo": 1}
    assert result["notification"]["id"] == "n-1"


@pytest.mark.asyncio
async def test_send_notification_requires_user_id() -> None:
    service = StubNotify()
    with pytest.raises(NotificationError) as exc:
        await send_notification(service, {})
    assert exc.value.code == "user_id_required"
