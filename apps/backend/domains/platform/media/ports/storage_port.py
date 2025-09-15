from __future__ import annotations

from typing import BinaryIO, Protocol


class IStorageGateway(Protocol):
    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str: ...


__all__ = ["IStorageGateway"]
