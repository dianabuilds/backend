from __future__ import annotations

from typing import Protocol, List


class IEmbeddingProvider(Protocol):
    @property
    def dim(self) -> int:  # pragma: no cover - контракт
        ...

    def embed(self, text: str) -> List[float]:  # pragma: no cover - контракт
        ...
