import logging
from typing import Callable, List

import requests

from app.core.config import settings
from .embedding import register_embedding_provider, simple_embedding, reduce_vector_dim

logger = logging.getLogger(__name__)


def _make_aimlapi_provider(api_base: str, api_key: str, model: str, target_dim: int) -> Callable[[str], List[float]]:
    """
    Возвращает функцию-провайдер для AIML API /v1/embeddings.
    """
    base = api_base.rstrip("/")

    def _provider(text: str) -> List[float]:
        url = base  # уже полный путь до /v1/embeddings из настроек
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": text,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Совместимо с форматом OpenAI: {"data":[{"embedding":[...]}], ...}
        try:
            embedding = data["data"][0]["embedding"]
        except Exception as e:
            logger.error("Invalid embedding response structure: %s; body=%s", e, data)
            raise
        # Приводим размерность к target_dim (например, 384)
        if len(embedding) != target_dim:
            return reduce_vector_dim([float(x) for x in embedding], target_dim)
        return [float(x) for x in embedding]

    return _provider


def configure_from_settings() -> None:
    """
    Конфигурирует провайдер эмбеддингов на основе настроек приложения.
    Поддерживаются: 'simple', 'aimlapi'.
    """
    backend = getattr(settings, "embedding_backend", "simple")
    dim = getattr(settings, "embedding_dim", 384)

    if backend == "simple":
        register_embedding_provider(simple_embedding, dim)
        logger.info("Embedding backend configured: simple (dim=%s)", dim)
        return

    if backend == "aimlapi":
        api_base = getattr(settings, "embedding_api_base", "").strip()
        api_key = getattr(settings, "embedding_api_key", "").strip()
        model = getattr(settings, "embedding_model", "").strip()
        if not api_base or not api_key or not model:
            logger.warning("AIML API embedding is misconfigured. Falling back to 'simple'.")
            register_embedding_provider(simple_embedding, dim)
            return
        provider = _make_aimlapi_provider(api_base=api_base, api_key=api_key, model=model, target_dim=dim)
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: aimlapi model=%s dim=%s", model, dim)
        return

    # Бэкенд не поддержан — откатываемся на simple
    logger.warning("Unknown embedding backend '%s'. Falling back to 'simple'.", backend)
    register_embedding_provider(simple_embedding, dim)


def configure_embedding_provider(func: Callable[[str], List[float]], dim: int) -> None:
    """
    Регистрирует пользовательский провайдер эмбеддингов из приложения.
    """
    register_embedding_provider(func, dim)


__all__ = [
    "configure_from_settings",
    "configure_embedding_provider",
]