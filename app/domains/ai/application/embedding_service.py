from __future__ import annotations

import hashlib
import logging
from typing import Callable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.domains.ai.application.ports.embedding_port import IEmbeddingProvider
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.models import Tag
from app.domains.tags.infrastructure.models.tag_models import NodeTag

logger = logging.getLogger(__name__)

# ВАЖНО: размер вектора должен совпадать со схемой БД (VECTOR(N) в моделях).
EMBEDDING_DIM = settings.embedding.dim

_provider: Optional[IEmbeddingProvider] = None


class _LambdaEmbeddingProvider:
    def __init__(self, fn: Callable[[str], List[float]], dim: int) -> None:
        self._fn = fn
        self._dim = int(dim)

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        return self._fn(text)


def reduce_vector_dim(src: List[float], target_dim: int) -> List[float]:
    if target_dim <= 0:
        raise ValueError("target_dim must be > 0")
    acc = [0.0] * target_dim
    for i, v in enumerate(src):
        acc[i % target_dim] += float(v)
    norm = (sum(x * x for x in acc)) ** 0.5
    if norm:
        acc = [x / norm for x in acc]
    return acc


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def register_embedding_provider(func: Callable[[str], List[float]], dim: int) -> None:
    """Регистрация кастомного провайдера (совместимость со старым API)."""
    global _provider
    _provider = _LambdaEmbeddingProvider(func, dim)
    logger.info("Embedding provider registered: dim=%s", dim)
    if dim != EMBEDDING_DIM:
        logger.warning("Registered provider dim=%s, expected=%s", dim, EMBEDDING_DIM)


def set_embedding_provider(provider: IEmbeddingProvider) -> None:
    global _provider
    _provider = provider
    logger.info("Embedding provider set: dim=%s", provider.dim)
    if provider.dim != EMBEDDING_DIM:
        logger.warning("Provider dim=%s, expected=%s", provider.dim, EMBEDDING_DIM)


def _default_simple_embedding(text: str) -> List[float]:
    tokens = text.lower().split()
    vec = [0.0] * EMBEDDING_DIM
    for tok in tokens:
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        idx = h % EMBEDDING_DIM
        vec[idx] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm:
        vec = [v / norm for v in vec]
    return vec


def get_embedding(text: str) -> List[float]:
    global _provider
    if _provider is None:
        # провайдер по умолчанию
        _provider = _LambdaEmbeddingProvider(_default_simple_embedding, EMBEDDING_DIM)
    vec = _provider.embed(text)
    if len(vec) != EMBEDDING_DIM:
        logger.warning("Embedding size %s doesn't match expected %s; reducing", len(vec), EMBEDDING_DIM)
        vec = reduce_vector_dim(vec, EMBEDDING_DIM)
    return vec


async def update_node_embedding(db: AsyncSession, node: Node) -> None:
    """Compute and store embedding for a node with safe dimensionality."""
    def _db_embedding_dim() -> int:
        try:
            col = Node.__table__.c.embedding_vector  # type: ignore[attr-defined]
            dim = getattr(col.type, "dim", None) or getattr(col.type, "dims", None) or getattr(col.type, "dimensions", None)
            return int(dim) if dim else EMBEDDING_DIM
        except Exception:
            return EMBEDDING_DIM

    parts: list[str] = []
    if getattr(node, "title", None):
        parts.append(node.title)
    if getattr(node, "nodes", None) is not None:
        parts.append(str(node.content))
    try:
        res = await db.execute(
            select(Tag.slug).join(NodeTag, NodeTag.tag_id == Tag.id).where(NodeTag.node_id == node.id)
        )
        parts.extend([row[0] for row in res.all()])
    except Exception as e:
        logger.debug("Failed to fetch tag slugs for embedding (non-fatal): %s", e)

    text = " ".join(parts)
    vec = get_embedding(text)
    db_dim = _db_embedding_dim()
    if len(vec) != db_dim:
        logger.warning("Embedding length %s != DB column dim %s, adjusting", len(vec), db_dim)
        vec = reduce_vector_dim(vec, db_dim)

    try:
        node.embedding_vector = vec
        await db.flush()
        logger.info("Prepared embedding update for node %s (len=%d)", getattr(node, "slug", "?"), len(vec))
    except Exception as e:
        logger.exception(
            "Failed to prepare embedding for node %s: len=%d, db_dim=%d",
            getattr(node, "slug", "?"),
            len(vec),
            db_dim,
        )
        raise
