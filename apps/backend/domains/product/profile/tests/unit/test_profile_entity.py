from __future__ import annotations

from datetime import timedelta

import pytest

from domains.product.profile.adapters.repo_memory import MemoryRepo
from domains.product.profile.application.services import Service
from packages.core import Flags


class DummyOutbox:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        self.events.append((topic, payload))


class DummyIam:
    def allow(self, subject: dict, action: str, resource: dict) -> bool:
        return True


def make_service() -> Service:
    repo = MemoryRepo()
    return Service(repo=repo, outbox=DummyOutbox(), iam=DummyIam(), flags=Flags())


def test_update_profile_rate_limit():
    svc = make_service()
    subject = {"user_id": "u1"}

    result = svc.update_profile("u1", {"username": "first"}, subject=subject)
    assert result["username"] == "first"

    with pytest.raises(ValueError) as exc:
        svc.update_profile("u1", {"username": "second"}, subject=subject)
    assert str(exc.value) == "username_rate_limited"

    # simulate cooldown expiry
    repo = svc.repo  # type: ignore[attr-defined]
    profile = repo.get("u1")  # type: ignore[assignment]
    assert profile is not None
    profile.last_username_change_at = profile.last_username_change_at - timedelta(days=15)  # type: ignore[assignment]
    repo._profiles["u1"] = profile  # type: ignore[attr-defined]

    result = svc.update_profile("u1", {"username": "second"}, subject=subject)
    assert result["username"] == "second"


def test_request_email_change_and_confirm():
    svc = make_service()
    subject = {"user_id": "u1"}

    svc.update_profile("u1", {"username": "user"}, subject=subject)
    result = svc.request_email_change("u1", "test@example.com", subject=subject)
    token = result["token"]

    updated = svc.confirm_email_change("u1", token, subject=subject)
    assert updated["email"] == "test@example.com"

    # Further change blocked until cooldown passes
    with pytest.raises(ValueError) as exc:
        svc.request_email_change("u1", "next@example.com", subject=subject)
    assert str(exc.value) == "email_rate_limited"

    # simulate cooldown expiry and retry
    repo = svc.repo  # type: ignore[attr-defined]
    profile = repo.get("u1")  # type: ignore[assignment]
    profile.last_email_change_at = profile.last_email_change_at - timedelta(days=15)  # type: ignore[assignment]
    repo._profiles["u1"] = profile  # type: ignore[attr-defined]

    result = svc.request_email_change("u1", "next@example.com", subject=subject)
    token = result["token"]
    updated = svc.confirm_email_change("u1", token, subject=subject)
    assert updated["email"] == "next@example.com"
