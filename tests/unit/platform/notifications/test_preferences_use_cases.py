from __future__ import annotations

import logging
from typing import Any

import pytest

from domains.platform.notifications.application.dispatch_use_cases import (
    preview_channel_notification,
    send_channel_notification,
)
from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)
from domains.platform.notifications.application.preferences_use_cases import (
    get_preferences,
    set_preferences,
)


class StubPreferenceService:
    def __init__(self) -> None:
        self.get_calls: list[tuple[str, dict[str, Any] | None]] = []
        self.set_calls: list[tuple[str, dict[str, Any]]] = []
        self.preferences: dict[str, Any] = {"email": {"inbox": {"opt_in": True}}}

    async def get_preferences(
        self, user_id: str, *, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.get_calls.append((user_id, context))
        return dict(self.preferences)

    async def set_preferences(self, user_id: str, preferences: dict[str, Any]) -> None:
        self.set_calls.append((user_id, preferences))


class StubUsers:
    def __init__(self, user_id: str | None) -> None:
        self.user_id = user_id
        self.calls: list[str] = []

    async def get(self, identifier: str):
        self.calls.append(identifier)
        return type("User", (), {"id": self.user_id}) if self.user_id else None


@pytest.mark.asyncio
async def test_get_preferences_returns_payload() -> None:
    service = StubPreferenceService()
    users = StubUsers("user-42")

    result = await get_preferences(
        service,
        users,
        subject="external",
        context={"sub": "external"},
    )

    assert result["preferences"]["email"]["inbox"]["opt_in"] is True
    assert service.get_calls[0][0] == "user-42"


@pytest.mark.asyncio
async def test_set_preferences_requires_mapping() -> None:
    service = StubPreferenceService()
    users = StubUsers("user-42")
    with pytest.raises(NotificationError) as exc:
        await set_preferences(service, users, subject="external", preferences=None)
    assert exc.value.code == "invalid_preferences"


@pytest.mark.asyncio
async def test_set_preferences_persists_changes() -> None:
    service = StubPreferenceService()
    users = StubUsers("user-42")

    result = await set_preferences(
        service,
        users,
        subject="user-42",
        preferences={"email": {"inbox": {"opt_in": False}}},
    )

    assert result["ok"] is True
    assert service.set_calls == [("user-42", {"email": {"inbox": {"opt_in": False}}})]


def test_send_channel_notification_validates_schema() -> None:
    dispatched: list[tuple[str, dict[str, Any]]] = []

    def dispatcher(channel: str, payload: dict[str, Any]) -> None:
        dispatched.append((channel, payload))

    def validator(path: str, method: str, body: dict[str, Any]) -> None:
        if body.get("payload", {}).get("invalid"):
            raise ValueError("bad payload")

    with pytest.raises(NotificationError) as exc:
        send_channel_notification(
            dispatcher,
            validator,
            channel="log",
            payload={"invalid": True},
            validation_errors=(ValueError,),
        )
    assert exc.value.code == "schema_validation_failed"

    result = send_channel_notification(
        dispatcher,
        validator,
        channel="log",
        payload={"ok": True},
        validation_errors=(ValueError,),
    )

    assert result == {"ok": True}
    assert dispatched == [("log", {"ok": True})]


def test_test_channel_notification_handles_runtime_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def dispatcher(channel: str, payload: dict[str, Any]) -> None:
        raise RuntimeError("failed")

    with pytest.raises(NotificationError) as exc:
        preview_channel_notification(
            dispatcher, channel="log", payload=None, logger=logging.getLogger(__name__)
        )
    assert exc.value.code == "publish_failed"
