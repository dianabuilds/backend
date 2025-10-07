from __future__ import annotations

import io
from typing import Any

import pytest
import pytest_asyncio

from domains.product.profile.adapters.memory.repository import MemoryRepo
from domains.product.profile.application.commands import (
    bind_wallet,
    request_email_change,
    update_profile,
    upload_avatar,
)
from domains.product.profile.application.exceptions import ProfileError
from domains.product.profile.application.profile_presenter import profile_to_dict
from domains.product.profile.application.queries import get_profile_me
from domains.product.profile.application.services import Service
from domains.product.profile.domain.entities import Profile
from domains.platform.media.application.storage_service import StorageService
from packages.core import Flags


def _seed_profile(service: Service, user_id: str = "u1") -> None:
    repo = service.repo  # type: ignore[attr-defined]
    repo._profiles[user_id] = Profile(id=user_id)  # type: ignore[index]


class DummyOutbox:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def publish(
        self, topic: str, payload: dict[str, Any], key: str | None = None
    ) -> None:
        self.events.append((topic, payload))


class DummyIam:
    def allow(
        self, subject: dict[str, Any], action: str, resource: dict[str, Any]
    ) -> bool:
        return True


class DummyStorage:
    def __init__(self) -> None:
        self.saved: list[tuple[bytes, str, str]] = []

    def save(self, fileobj: io.BytesIO, filename: str, content_type: str) -> str:
        data = fileobj.read()
        self.saved.append((data, filename, content_type))
        return f"https://cdn.local/{filename}"


@pytest_asyncio.fixture()
async def service() -> Service:
    repo = MemoryRepo()
    svc = Service(repo=repo, outbox=DummyOutbox(), iam=DummyIam(), flags=Flags())
    _seed_profile(svc)
    await svc.update_profile("u1", {"username": "user"}, subject={"user_id": "u1"})
    return svc


@pytest.mark.asyncio
async def test_get_profile_me_returns_payload_and_etag(service: Service) -> None:
    payload, meta = await get_profile_me(service, "u1")
    assert meta.etag is not None
    assert payload["username"] == "user"


@pytest.mark.asyncio
async def test_update_profile_requires_if_match(service: Service) -> None:
    subject = {"user_id": "u1"}

    with pytest.raises(ProfileError) as exc:
        await update_profile(
            service,
            "u1",
            {"bio": "new"},
            subject=subject,
            if_match=None,
        )
    assert exc.value.code == "E_ETAG_REQUIRED"

    _, current_meta = await get_profile_me(service, "u1")

    payload, meta = await update_profile(
        service,
        "u1",
        {"bio": "new"},
        subject=subject,
        if_match=current_meta.etag,
    )
    assert payload["bio"] == "new"
    assert meta.etag is not None and meta.etag != current_meta.etag


@pytest.mark.asyncio
async def test_request_email_change_returns_token(service: Service) -> None:
    subject = {"user_id": "u1"}
    payload, meta = await request_email_change(
        service, "u1", "test@example.com", subject=subject
    )
    assert meta.status_code == 200
    assert payload["status"] == "pending"
    assert "token" in payload


@pytest.mark.asyncio
async def test_bind_wallet_strips_whitespace(service: Service) -> None:
    subject = {"user_id": "u1"}
    payload, _ = await bind_wallet(
        service,
        "u1",
        {"address": " 0xabc ", "chain_id": " 1 ", "signature": None},
        subject=subject,
    )
    profile = profile_to_dict(await service.get_profile("u1"))
    assert profile["wallet"]["address"] == "0xabc"
    assert profile["wallet"]["chain_id"] == "1"
    assert payload["wallet"]["address"] == "0xabc"


@pytest.mark.asyncio
async def test_upload_avatar_validates_input(service: Service) -> None:
    storage_backend = DummyStorage()
    storage = StorageService(storage_backend)

    with pytest.raises(ProfileError) as exc:
        await upload_avatar(
            storage,
            file_name="avatar.png",
            content=b"data",
            content_type="image/gif",
            max_size=10,
            allowed_types={"image/png"},
        )
    assert exc.value.code == "unsupported_media_type"

    payload, meta = await upload_avatar(
        storage,
        file_name="avatar.png",
        content=b"data",
        content_type="image/png",
        max_size=10,
        allowed_types={"image/png"},
    )
    assert payload["success"] == 1
    assert meta.status_code == 200
    assert storage_backend.saved[0][1] == "avatar.png"
