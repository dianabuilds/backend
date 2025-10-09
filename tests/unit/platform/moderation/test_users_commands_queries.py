from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from domains.platform.moderation.application.users import commands, queries
from domains.platform.moderation.application.users.exceptions import (
    ModerationUserError,
    UserNotFoundError,
)


class DummySettings(SimpleNamespace):
    database_url: str | None = None


async def _async_noop(*args: Any, **kwargs: Any) -> None:
    return None


@pytest.mark.asyncio
async def test_list_users_view_fallback(monkeypatch):
    async def fake_list(*args, **kwargs):
        return {"items": [{"id": "1", "username": "demo"}], "next_cursor": None}

    monkeypatch.setattr(queries, "list_users", fake_list)

    result = await queries.list_users_view(
        SimpleNamespace(),
        settings=None,
        repository=None,
        status=None,
        role=None,
        registered_from=None,
        registered_to=None,
        q=None,
        limit=10,
        cursor=None,
    )

    assert result == {
        "items": [{"id": "1", "username": "demo"}],
        "next_cursor": None,
    }


class DummyRepository:
    def __init__(self) -> None:
        self.calls: dict[str, Any] = {}

    async def list_users(self, **kwargs: Any) -> dict[str, Any] | None:
        self.calls["list_users"] = kwargs
        return {"items": [{"id": "sql", "username": "db"}], "next_cursor": "5"}

    async def update_roles(self, user_id: str, add, remove):
        self.calls["update_roles"] = {
            "user_id": user_id,
            "add": list(add),
            "remove": list(remove),
        }
        return ["Admin"]


@pytest.mark.asyncio
async def test_list_users_view_uses_repository():
    repo = DummyRepository()
    result = await queries.list_users_view(
        SimpleNamespace(),
        settings=DummySettings(),
        repository=repo,
        limit=5,
    )
    assert result["items"][0]["id"] == "sql"
    assert repo.calls["list_users"]["limit"] == 5


@pytest.mark.asyncio
async def test_get_user_view_service_not_found(monkeypatch):
    async def fake_get(*args, **kwargs):
        raise KeyError("missing")

    monkeypatch.setattr(queries, "get_user", fake_get)

    with pytest.raises(UserNotFoundError):
        await queries.get_user_view(SimpleNamespace(), "missing")


@pytest.mark.asyncio
async def test_update_roles_command_requires_repository():
    with pytest.raises(ModerationUserError):
        await commands.update_roles_command(
            SimpleNamespace(update_roles=_async_noop),
            "42",
            {"add": ["admin"], "remove": []},
            settings=None,
            repository=None,
        )


@pytest.mark.asyncio
async def test_issue_sanction_value_error(monkeypatch):
    async def fake_issue(*args, **kwargs):
        raise ValueError("bad payload")

    monkeypatch.setattr(commands, "ensure_user_stub", _async_noop)
    service = SimpleNamespace(
        issue_sanction=fake_issue,
        ensure_user_stub=_async_noop,
    )

    with pytest.raises(ModerationUserError) as err:
        await commands.issue_sanction(
            service,
            "1",
            {},
            settings=None,
            notifications=None,
            repository=None,
        )
    assert err.value.status_code == 400


@pytest.mark.asyncio
async def test_add_note_requires_text():
    service = SimpleNamespace(add_note=_async_noop, ensure_user_stub=_async_noop)
    with pytest.raises(ModerationUserError):
        await commands.add_note(
            service,
            "1",
            {"text": "   "},
            settings=None,
            repository=None,
        )
