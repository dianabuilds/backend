from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

import httpx


class HttpClient:
    """Thin async wrapper around httpx.AsyncClient with lifecycle helpers."""

    def __init__(
        self,
        timeout: float = 5.0,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None
        self._closed = False

    async def __aenter__(self) -> HttpClient:
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("HttpClient is closed")

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            await self._client.aclose()

    async def close(self) -> None:
        await self.aclose()

    async def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        self._ensure_open()
        return await self._client.get(url, params=params)

    async def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
    ) -> httpx.Response:
        self._ensure_open()
        return await self._client.post(url, json=json, data=data)

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        self._ensure_open()
        return await self._client.request(method, url, **kwargs)

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client
