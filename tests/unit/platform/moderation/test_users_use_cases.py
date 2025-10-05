from types import SimpleNamespace

import pytest

from apps.backend.domains.platform.moderation.application.users import use_cases
from apps.backend.domains.platform.moderation.application.users.exceptions import (
    ModerationUserError,
    UserNotFoundError,
)


class DummySettings(SimpleNamespace):
    database_url: str | None = None


async def _async_noop(*args, **kwargs):
    return None


@pytest.mark.asyncio
async def test_list_users_fallback_to_service(monkeypatch):
    async def fake_list(*args, **kwargs):
        return {"items": [{"id": "1", "username": "demo"}], "next_cursor": None}

    monkeypatch.setattr(use_cases, "_build_engine", lambda *args, **kwargs: None)
    monkeypatch.setattr(use_cases, "service_list_users", fake_list)

    result = await use_cases.list_users(
        service=SimpleNamespace(),
        settings=DummySettings(),
        status=None,
        role=None,
        registered_from=None,
        registered_to=None,
        q=None,
        limit=10,
        cursor=None,
    )
    assert isinstance(result, use_cases.UseCaseResult)
    assert result.payload == {
        "items": [{"id": "1", "username": "demo"}],
        "next_cursor": None,
    }


@pytest.mark.asyncio
async def test_get_user_service_not_found(monkeypatch):
    async def fake_get(*args, **kwargs):
        raise KeyError("missing")

    monkeypatch.setattr(use_cases, "_build_engine", lambda *args, **kwargs: None)
    monkeypatch.setattr(use_cases, "service_get_user", fake_get)

    with pytest.raises(UserNotFoundError):
        await use_cases.get_user(SimpleNamespace(), DummySettings(), "missing")


@pytest.mark.asyncio
async def test_update_roles_requires_engine(monkeypatch):
    monkeypatch.setattr(use_cases, "_build_engine", lambda *args, **kwargs: None)
    with pytest.raises(ModerationUserError):
        await use_cases.update_roles_use_case(
            SimpleNamespace(update_roles=_async_noop),
            DummySettings(),
            "42",
            {"add": ["admin"], "remove": []},
        )


@pytest.mark.asyncio
async def test_issue_sanction_value_error(monkeypatch):
    async def fake_issue(*args, **kwargs):
        raise ValueError("bad payload")

    service = SimpleNamespace(
        issue_sanction=fake_issue,
        ensure_user_stub=_async_noop,
    )
    monkeypatch.setattr(use_cases, "_build_engine", lambda *args, **kwargs: None)

    with pytest.raises(ModerationUserError) as err:
        await use_cases.issue_sanction(
            service,
            DummySettings(),
            notifications=None,
            user_id="1",
            body={},
            idempotency_key=None,
        )
    assert err.value.status_code == 400


@pytest.mark.asyncio
async def test_add_note_requires_text(monkeypatch):
    monkeypatch.setattr(use_cases, "_build_engine", lambda *args, **kwargs: None)
    service = SimpleNamespace(add_note=_async_noop)
    with pytest.raises(ModerationUserError):
        await use_cases.add_note(service, DummySettings(), "1", {"text": "   "})
