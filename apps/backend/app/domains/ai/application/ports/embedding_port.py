from __future__ import annotations

from typing import Protocol


class IEmbeddingProvider(Protocol):
    @property
    def dim(self) -> int:  # pragma: no cover - контракт
        ...

    def embed(self, text: str) -> list[float]:  # pragma: no cover - контракт
        ...
