from __future__ import annotations


class ModerationContentError(Exception):
    def __init__(
        self, *, code: str, status_code: int, message: str | None = None
    ) -> None:
        self.code = code
        self.status_code = int(status_code)
        self.message = message or code
        super().__init__(self.message)


__all__ = ["ModerationContentError"]
