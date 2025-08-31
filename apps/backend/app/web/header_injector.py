from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


class HeaderInjector:
    """
    Простейшая ASGI-обёртка, добавляющая/переопределяющая заголовки ответа.
    Используется для смонтированных приложений (StaticFiles), которые обходят middleware основного приложения.
    """

    def __init__(self, app, headers: dict[str, str]) -> None:
        self.app = app
        self.headers = headers

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ) -> None:
        async def send_wrapper(message: dict) -> None:
            if message.get("type") == "http.response.start":
                raw_headers = list(message.get("headers", []))
                # Дополняем или переопределяем заголовки
                existing = {k.decode().lower(): (k, v) for k, v in raw_headers}
                for k, v in self.headers.items():
                    key_bytes = k.encode()
                    val_bytes = v.encode()
                    if k.lower() in existing:
                        idx = raw_headers.index(existing[k.lower()])
                        raw_headers[idx] = (key_bytes, val_bytes)
                    else:
                        raw_headers.append((key_bytes, val_bytes))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
