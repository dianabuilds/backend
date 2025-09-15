from __future__ import annotations

import httpx


class HttpClient:
    def __init__(self, timeout: float = 5.0):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get(self, url: str) -> httpx.Response:
        return await self._client.get(url)

    async def post(self, url: str, json: dict) -> httpx.Response:  # noqa: A002
        return await self._client.post(url, json=json)
