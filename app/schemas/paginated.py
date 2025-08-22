from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class Paginated(GenericModel, Generic[T]):
    page: int
    per_page: int
    total: int
    items: List[T]
