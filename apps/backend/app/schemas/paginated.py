from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    page: int
    per_page: int
    total: int
    items: List[T]
