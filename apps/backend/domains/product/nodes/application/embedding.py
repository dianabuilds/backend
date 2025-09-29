from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

import httpx

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(
        self,
        *,
        base_url: str | None,
        model: str | None,
        api_key: str | None,
        provider: str | None = None,
        timeout: float = 10.0,
        connect_timeout: float = 2.0,
        retries: int = 3,
        enabled: bool = True,
    ) -> None:
        clean_base = base_url.rstrip("/") if base_url else None
        if clean_base and clean_base.lower().endswith("/embeddings"):
            clean_base = clean_base[: -len("/embeddings")]
        self._base_url = clean_base
        self._model = model
        self._api_key = api_key
        self._provider = provider or "aimlapi"
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._retries = max(0, retries)
        self._enabled = enabled and bool(self._base_url and self._model)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def provider(self) -> str | None:
        return self._provider

    async def embed(self, text: str) -> list[float] | None:
        if not self._enabled:
            return None
        url = f"{self._base_url}/embeddings" if self._base_url else None
        if url is None:
            return None
        payload = {"model": self._model, "input": text}
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        attempt = 0
        last_error: Exception | None = None
        while attempt <= self._retries:
            try:
                timeout = httpx.Timeout(self._timeout, connect=self._connect_timeout)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                embedding = self._extract_embedding(data)
                if embedding is None:
                    logger.warning(
                        "embedding_response_missing_data",
                        extra={"provider": self._provider},
                    )
                    return None
                return [float(v) for v in embedding]
            except Exception as exc:  # pragma: no cover - network failure path
                last_error = exc
                attempt += 1
                if attempt > self._retries:
                    break
                backoff = min(1.0 * attempt, 5.0)
                await asyncio.sleep(backoff)
        if last_error is not None:
            logger.warning("embedding_generation_failed", exc_info=last_error)
        return None

    def _extract_embedding(self, data: dict) -> Sequence[float] | None:
        try:
            items = data.get("data")
            if not items:
                return None
            first = items[0]
            embedding = first.get("embedding")
            if embedding is None:
                return None
            return embedding
        except Exception:
            return None
