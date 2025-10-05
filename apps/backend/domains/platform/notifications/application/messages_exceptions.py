from __future__ import annotations

from collections.abc import Mapping


class NotificationError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.code = code
        self.status_code = int(status_code)
        self.message = message or code
        self.headers = dict(headers or {})
        super().__init__(self.message)


__all__ = ["NotificationError"]
