from __future__ import annotations

import hashlib

from app.core.config import settings
from app.domains.ai.application.ports.embedding_port import IEmbeddingProvider


class SimpleEmbeddingProvider(IEmbeddingProvider):
    def __init__(self, dim: int | None = None) -> None:
        self._dim = int(dim or settings.embedding.dim)

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        tokens = text.lower().split()
        vec = [0.0] * self._dim
        for tok in tokens:
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm:
            vec = [v / norm for v in vec]
        return vec
