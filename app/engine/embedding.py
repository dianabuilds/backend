from __future__ import annotations

import hashlib
import logging
from typing import Callable, List, Optional
import os
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.node import Node

logger = logging.getLogger(__name__)

# ВАЖНО: размер вектора должен совпадать со схемой БД (VECTOR(384) в моделях).
# Менять embedding_dim без миграции нельзя.
EMBEDDING_DIM = getattr(settings, "embedding_dim", 384)
if EMBEDDING_DIM != 384:
    logger.warning(
        "embedding_dim=%s отличается от 384, возможно потребуется миграция схемы.",
        EMBEDDING_DIM,
    )

# Глобальный провайдер эмбеддингов
_provider_func: Callable[[str], List[float]] | None = None
_provider_dim: int = EMBEDDING_DIM


def _extract_text(node: Node) -> str:
    parts = []
    if node.title:
        parts.append(node.title)
    if node.content is not None:
        parts.append(str(node.content))
    parts.extend(node.tag_slugs)
    return " ".join(parts)


def simple_embedding(text: str) -> List[float]:
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


def reduce_vector_dim(src: List[float], target_dim: int) -> List[float]:
    """
    Сводит вектор произвольной длины к target_dim путём агрегирования по модулю.
    Затем нормализует результат до единичной длины.
    """
    if target_dim <= 0:
        raise ValueError("target_dim must be > 0")
    acc = [0.0] * target_dim
    for i, v in enumerate(src):
        acc[i % target_dim] += float(v)
    norm = sum(x * x for x in acc) ** 0.5
    if norm:
        acc = [x / norm for x in acc]
    return acc


def register_embedding_provider(func: Callable[[str], List[float]], dim: int) -> None:
    """
    Регистрирует функцию-провайдер эмбеддингов.
    func: функция, принимающая текст и возвращающая вектор эмбеддинга.
    dim: размерность эмбеддинга.
    """
    global _provider_func, _provider_dim
    _provider_func = func
    _provider_dim = dim
    logger.info("Embedding provider registered: dim=%s", dim)
    if _provider_dim != 384:
        logger.warning(
            "Зарегистрирован провайдер с размерностью %s. Убедитесь, что колонка VECTOR в БД совместима.",
            _provider_dim,
        )


def get_embedding(text: str) -> List[float]:
    """
    Возвращает эмбеддинг текста, используя зарегистрированный провайдер.
    По умолчанию используется simple_embedding.
    """
    if _provider_func is None:
        # Инициализация провайдера по умолчанию
        register_embedding_provider(simple_embedding, EMBEDDING_DIM)
    return _provider_func(text)  # type: ignore[operator]


async def update_node_embedding(db: AsyncSession, node: Node) -> None:
    """Compute and store embedding for a node."""
    text = _extract_text(node)
    node.embedding_vector = simple_embedding(text)
    await db.commit()
    await db.refresh(node)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
