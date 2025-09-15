from __future__ import annotations

from collections.abc import Sequence

from ..application.ports import ProductDTO, Repo


class SQLRepo(Repo):
    """
    SQLAlchemy 2.x repository implementation template for Product.

    Replace session plumbing with your project's DB session management.
    This template intentionally avoids importing SQLAlchemy to keep it lightweight.
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        # TODO: inject Engine/Session factory

    async def get(self, product_id: str) -> ProductDTO | None:  # type: ignore[override]
        raise NotImplementedError

    async def list_by_owner(
        self, owner_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[ProductDTO]:  # type: ignore[override]
        raise NotImplementedError

    async def upsert(self, product: ProductDTO) -> None:  # type: ignore[override]
        raise NotImplementedError

    async def delete(self, product_id: str) -> bool:  # type: ignore[override]
        raise NotImplementedError
