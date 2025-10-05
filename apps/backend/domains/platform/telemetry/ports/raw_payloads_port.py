from __future__ import annotations

from typing import Protocol


class IRawPayloadStore(Protocol):
    def put_text(
        self, prefix: str, data: str, *, filename_hint: str | None = None
    ) -> str: ...


__all__ = ["IRawPayloadStore"]
