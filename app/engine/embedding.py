from __future__ import annotations

from __future__ import annotations

import hashlib
import logging
from typing import Callable, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.node import Node
from app.models.tag import Tag, NodeTag

logger = logging.getLogger(__name__)

# ВАЖНО: размер вектора должен совпадать со схемой БД (VECTOR(N) в моделях).
# Менять embedding_dim без миграции нельзя.
EMBEDDING_DIM = settings.embedding.dim

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
    if _provider_dim != EMBEDDING_DIM:
        logger.warning(
            "Зарегистрирован провайдер с размерностью %s, ожидалась %s.",
            _provider_dim,
            EMBEDDING_DIM,
        )


def get_embedding(text: str) -> List[float]:
    """
    Возвращает эмбеддинг текста, используя зарегистрированный провайдер.
    По умолчанию используется simple_embedding.
    """
    if _provider_func is None:
        # Инициализация провайдера по умолчанию
        register_embedding_provider(simple_embedding, EMBEDDING_DIM)
    vec = _provider_func(text)  # type: ignore[operator]
    # Провайдер может возвращать вектор произвольной длины. Если он не
    # совпадает с размерностью, ожидаемой БД, приводим его к нужному
    # размеру. Без этого попытка сохранить вектор вызовет ошибку
    # "dimension mismatch" и приведёт к HTTP 500 при создании узла.
    if len(vec) != EMBEDDING_DIM:
        logger.warning(
            "Embedding size %s doesn't match expected %s; reducing",
            len(vec),
            EMBEDDING_DIM,
        )
        vec = reduce_vector_dim(vec, EMBEDDING_DIM)
    return vec


async def update_node_embedding(db: AsyncSession, node: Node) -> None:
    """Compute and store embedding for a node.

    Перед записью в БД приводим размер эмбеддинга к фактической размерности
    колонки embedding_vector, чтобы избежать ошибок наподобие
    "dimension mismatch" при коммите.
    """
    # Пытаемся определить ожидаемую БД размерность из типа столбца
    def _db_embedding_dim() -> int:
        try:
            col = Node.__table__.c.embedding_vector  # type: ignore[attr-defined]
            # В разных реализациях pgvector атрибут может называться по-разному
            dim = (
                getattr(col.type, "dim", None)
                or getattr(col.type, "dims", None)
                or getattr(col.type, "dimensions", None)
            )
            return int(dim) if dim else EMBEDDING_DIM
        except Exception:
            return EMBEDDING_DIM

    # Собираем текст для эмбеддинга без ленивой загрузки отношений.
    parts: list[str] = []
    if getattr(node, "title", None):
        parts.append(node.title)
    if getattr(node, "content", None) is not None:
        parts.append(str(node.content))
    # Получаем слаги тегов явным запросом, чтобы не триггерить lazy-load в AsyncSession
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
        logger.warning(
            "Embedding length %s != DB column dim %s, adjusting",
            len(vec),
            db_dim,
        )
        vec = reduce_vector_dim(vec, db_dim)

    try:
        node.embedding_vector = vec
        await db.flush()
        logger.info(
            "Prepared embedding update for node %s (len=%d)",
            getattr(node, "slug", "?"),
            len(vec),
        )
    except Exception as e:
        logger.exception(
            "Failed to prepare embedding for node %s: len=%d, db_dim=%d",
            getattr(node, "slug", "?"),
            len(vec),
            db_dim,
        )
        raise


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
