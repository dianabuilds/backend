from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

# Domain-facing DTOs used by the application service boundary.


@dataclass(slots=True)
class ProductDTO:
    id: str
    owner_id: str
    name: str
    is_active: bool


@dataclass(slots=True)
class CreateProductInput:
    owner_id: str
    name: str


@dataclass(slots=True)
class UpdateProductInput:
    id: str
    name: str | None = None
    is_active: bool | None = None


@dataclass(slots=True)
class QuotaDecision:
    allow: bool
    remaining: int | None = None
    reason: str | None = None


@runtime_checkable
class Repo(Protocol):
    async def get(self, product_id: str) -> ProductDTO | None: ...

    async def list_by_owner(
        self, owner_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[ProductDTO]: ...

    async def upsert(self, product: ProductDTO) -> None: ...

    async def delete(self, product_id: str) -> bool: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class IamClient(Protocol):
    async def has_permission(self, user_id: str, permission: str) -> bool: ...

    async def get_premium_level(self, user_id: str) -> int: ...

    async def get_tags(self, user_id: str) -> set[str]: ...


# Optional feature flags container; keep minimal to avoid coupling.
@dataclass(slots=True)
class Flags:
    # In real code import from core.flags; here kept local for template reuse.
    allow_create_without_premium: bool = True
