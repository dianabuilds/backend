from __future__ import annotations

from typing import Protocol


class _Repo(Protocol):  # narrow type for local use
    async def get_name(self, id_: int) -> str | None:  # pragma: no cover - contract
        ...


class ExampleService:
    def __init__(self, repo: _Repo) -> None:
        self._repo = repo

    async def greet(self, id_: int) -> str:
        name = await self._repo.get_name(id_)
        return f"hello {name or 'world'}"

__all__ = ["ExampleService"]

