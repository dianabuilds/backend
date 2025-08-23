from __future__ import annotations

import logging
from typing import Callable, List

import requests

from app.core.config import settings
from app.domains.ai.application.embedding_service import (
    EMBEDDING_DIM,
    register_embedding_provider,
    reduce_vector_dim,
)
from app.domains.ai.infrastructure.providers.simple_embedding import SimpleEmbeddingProvider

logger = logging.getLogger(__name__)

def _simple_embedding(text: str) -> List[float]:
    return SimpleEmbeddingProvider(EMBEDDING_DIM).embed(text)


def _make_openai_provider(api_base: str, api_key: str, model: str, target_dim: int) -> Callable[[str], List[float]]:
    base = (api_base or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/embeddings"

    def _provider(text: str) -> List[float]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "input": text}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        embedding = data["data"][0]["embedding"]
        if len(embedding) != target_dim:
            return reduce_vector_dim([float(x) for x in embedding], target_dim)
        return [float(x) for x in embedding]

    return _provider


def _make_cohere_provider(api_base: str, api_key: str, model: str, target_dim: int) -> Callable[[str], List[float]]:
    url = (api_base or "https://api.cohere.ai/v1/embed").rstrip("/")

    def _provider(text: str) -> List[float]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "texts": [text]}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("embeddings", [[]])[0]
        if len(embedding) != target_dim:
            return reduce_vector_dim([float(x) for x in embedding], target_dim)
        return [float(x) for x in embedding]

    return _provider


def _make_hf_provider(api_base: str, api_key: str, model: str, target_dim: int) -> Callable[[str], List[float]]:
    base = api_base.rstrip("/") if api_base else f"https://api-inference.huggingface.co/models/{model}"

    def _provider(text: str) -> List[float]:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        payload = {"inputs": text}
        resp = requests.post(base, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "embedding" in data:
            embedding = data["embedding"]
        elif isinstance(data, list):
            first = data[0]
            embedding = first.get("embedding") if isinstance(first, dict) else first
        else:
            embedding = data
        if len(embedding) != target_dim:
            return reduce_vector_dim([float(x) for x in embedding], target_dim)
        return [float(x) for x in embedding]

    return _provider


def _make_local_provider(model: str, target_dim: int) -> Callable[[str], List[float]]:
    try:  # pragma: no cover - optional dependency
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as exc:  # pragma: no cover
        logger.warning("sentence-transformers not available: %s", exc)
        return _simple_embedding

    model_name = model or "sentence-transformers/all-MiniLM-L6-v2"
    st_model = SentenceTransformer(model_name)

    def _provider(text: str) -> List[float]:
        vec = st_model.encode(text).tolist()
        if len(vec) != target_dim:
            return reduce_vector_dim([float(x) for x in vec], target_dim)
        return [float(x) for x in vec]

    return _provider


def _make_aimlapi_provider(api_base: str, api_key: str, model: str, target_dim: int) -> Callable[[str], List[float]]:
    base = api_base.rstrip("/")

    def _provider(text: str) -> List[float]:
        url = base  # полный путь до /v1/embeddings
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "input": text}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        try:
            embedding = data["data"][0]["embedding"]
        except Exception as e:
            logger.error("Invalid embedding response structure: %s; body=%s", e, data)
            raise
        if len(embedding) != target_dim:
            return reduce_vector_dim([float(x) for x in embedding], target_dim)
        return [float(x) for x in embedding]

    return _provider


def configure_from_settings() -> None:
    """Configure embedding provider based on application settings (domain)."""
    backend = settings.embedding.name
    dim = settings.embedding.dim or EMBEDDING_DIM

    if backend == "simple":
        register_embedding_provider(_simple_embedding, dim)
        logger.info("Embedding backend configured: simple (dim=%s)", dim)
        return

    if backend == "openai":
        if not settings.embedding.api_key or not settings.embedding.model:
            logger.warning("OpenAI embedding is misconfigured. Falling back to 'simple'.")
            register_embedding_provider(_simple_embedding, dim)
            return
        provider = _make_openai_provider(
            api_base=settings.embedding.api_base,
            api_key=settings.embedding.api_key,
            model=settings.embedding.model,
            target_dim=dim,
        )
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: openai model=%s dim=%s", settings.embedding.model, dim)
        return

    if backend == "cohere":
        if not settings.embedding.api_key or not settings.embedding.model:
            logger.warning("Cohere embedding is misconfigured. Falling back to 'simple'.")
            register_embedding_provider(_simple_embedding, dim)
            return
        provider = _make_cohere_provider(
            api_base=settings.embedding.api_base,
            api_key=settings.embedding.api_key,
            model=settings.embedding.model,
            target_dim=dim,
        )
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: cohere model=%s dim=%s", settings.embedding.model, dim)
        return

    if backend == "huggingface":
        if not settings.embedding.model:
            logger.warning("HuggingFace embedding is misconfigured. Falling back to 'simple'.")
            register_embedding_provider(_simple_embedding, dim)
            return
        provider = _make_hf_provider(
            api_base=settings.embedding.api_base,
            api_key=settings.embedding.api_key,
            model=settings.embedding.model,
            target_dim=dim,
        )
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: huggingface model=%s dim=%s", settings.embedding.model, dim)
        return

    if backend == "local":
        provider = _make_local_provider(model=settings.embedding.model, target_dim=dim)
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: local model=%s dim=%s", settings.embedding.model, dim)
        return

    if backend == "aimlapi":
        api_base = (settings.embedding.api_base or "").strip()
        api_key = (settings.embedding.api_key or "").strip()
        model = (settings.embedding.model or "").strip()
        if not api_base or not api_key or not model:
            logger.warning("AIML API embedding is misconfigured. Falling back to 'simple'.")
            register_embedding_provider(_simple_embedding, dim)
            return
        provider = _make_aimlapi_provider(api_base=api_base, api_key=api_key, model=model, target_dim=dim)
        register_embedding_provider(provider, dim)
        logger.info("Embedding backend configured: aimlapi model=%s dim=%s", model, dim)
        return

    logger.warning("Unknown embedding backend '%s'. Falling back to 'simple'.", backend)
    register_embedding_provider(_simple_embedding, dim)


def configure_embedding_provider(func: Callable[[str], List[float]], dim: int) -> None:
    """Register custom embedding provider (domain-level hook)."""
    register_embedding_provider(func, dim)


__all__ = ["configure_from_settings", "configure_embedding_provider"]
