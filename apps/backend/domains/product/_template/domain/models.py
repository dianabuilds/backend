from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True, frozen=True)
class ProductId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Product:
    id: ProductId
    owner_id: str
    name: str
    is_active: bool = True
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    def rename(self, new_name: str) -> None:
        if not new_name or len(new_name.strip()) < 3:
            raise ValueError("product name must be at least 3 characters")
        self.name = new_name.strip()
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True, frozen=True)
class ProductEvent:
    type: str
    payload: dict
