from __future__ import annotations

from typing import Protocol, runtime_checkable

from domains.product.profile.domain.entities import Profile


@runtime_checkable
class Repo(Protocol):
    def get(self, id: str) -> Profile | None: ...  # noqa: A002
    def upsert(self, p: Profile) -> Profile: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class IamClient(Protocol):
    def allow(self, subject: dict, action: str, resource: dict) -> bool: ...
