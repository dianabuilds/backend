from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from datetime import UTC, datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domains.platform.notifications.application.interactors.commands import (
    NotificationCreateCommand,
)
from domains.platform.notifications.application.messages_use_cases import (
    list_notifications as list_notifications_use_case,
    mark_notification_read as mark_notification_read_use_case,
)


class StubNotificationRepo:
    def __init__(self) -> None:
        self.items: dict[str, list[dict[str, object]]] = {}

    async def list_for_user(
        self,
        user_id: str,
        *,
        placement: str,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int, int]:
        records = list(self.items.get(user_id, []))
        total = len(records)
        unread = sum(1 for record in records if not record.get("read_at"))
        return records, total, unread

    async def mark_read(self, user_id: str, notif_id: str) -> dict[str, object] | None:
        records = self.items.get(user_id)
        if not records:
            return None
        for index, record in enumerate(records):
            if record["id"] == notif_id:
                updated = dict(record)
                updated["read_at"] = datetime.now(UTC)
                records[index] = updated
                return updated
        return None


class StubUsersService:
    async def get(self, identifier: str) -> SimpleNamespace | None:
        if not identifier:
            return None
        return SimpleNamespace(id=identifier)


def _build_client(
    repo: StubNotificationRepo, users_service: StubUsersService, claims: dict[str, str]
) -> TestClient:
    app = FastAPI()

    @app.get("/v1/notifications")
    async def list_my_notifications(limit: int = 50, offset: int = 0):
        return await list_notifications_use_case(
            repo,
            users_service,
            subject=claims["sub"],
            placement="inbox",
            limit=limit,
            offset=offset,
        )

    @app.post("/v1/notifications/read/{notif_id}")
    async def mark_read(notif_id: str):
        return await mark_notification_read_use_case(
            repo,
            users_service,
            subject=claims["sub"],
            notification_id=notif_id,
        )

    return TestClient(app)


def test_notifications_list_and_mark_read() -> None:
    user_id = str(uuid4())
    claims = {"sub": user_id}
    repo = StubNotificationRepo()
    users = StubUsersService()

    command = NotificationCreateCommand(
        user_id=user_id,
        title="Integration Notification",
        message="Hot path notification",
        type_="system",
        placement="inbox",
        priority="normal",
        meta={"scope": "integration"},
    )
    dto = command.to_repo_payload()
    dto.update({"id": "notif-1", "read_at": None, "created_at": datetime.now(UTC)})
    repo.items[user_id] = [dto]

    client = _build_client(repo, users, claims)

    list_response = client.get("/v1/notifications")
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    assert body.get("items"), "expected items in response"
    item = body["items"][0]
    assert item["id"] == "notif-1"
    assert item["is_read"] is False
    assert body["unread"] == 1
    assert body["unread_total"] == 1
    assert body["total"] == 1
    assert body["has_more"] is False
    assert body["limit"] == 50
    assert body["offset"] == 0

    mark_response = client.post("/v1/notifications/read/notif-1")
    assert mark_response.status_code == 200, mark_response.text
    payload = mark_response.json()
    marked = payload["notification"]
    assert marked["id"] == "notif-1"
    assert marked["is_read"] is True
