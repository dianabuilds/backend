from __future__ import annotations


class BroadcastError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str | None = None,
    ) -> None:
        self.code = code
        self.status_code = int(status_code)
        self.message = message or code
        super().__init__(self.message)
        self.headers: dict[str, str] = {}


__all__ = ["BroadcastError"]
