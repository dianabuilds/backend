from __future__ import annotations

from typing import Protocol


class IPasswordHasher(Protocol):
    def hash(self, plain: str) -> str:  # pragma: no cover - контракт
        ...

    def verify(self, plain: str, hashed: str) -> bool:  # pragma: no cover - контракт
        ...
