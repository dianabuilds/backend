from __future__ import annotations

from typing import Optional, Protocol


class IRawPayloadStore(Protocol):
    def put_text(self, prefix: str, data: str, *, filename_hint: Optional[str] = None) -> str:  # pragma: no cover - контракт
        ...
