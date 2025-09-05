from __future__ import annotations

from typing import Any

import httpx

DEFAULT_TIMEOUT = 10.0


class HttpClient(httpx.AsyncClient):
    """Async HTTP client with default timeout and redirect handling."""

    def __init__(
        self,
        *,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        follow_redirects: bool = True,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("timeout", timeout)
        kwargs.setdefault("follow_redirects", follow_redirects)
        super().__init__(**kwargs)


def create_http_client(**kwargs: Any) -> HttpClient:
    """Factory returning :class:`HttpClient` instances."""
    return HttpClient(**kwargs)
