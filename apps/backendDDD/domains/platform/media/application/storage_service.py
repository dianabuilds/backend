from __future__ import annotations

from typing import BinaryIO

from apps.backendDDD.domains.platform.media.ports.storage_port import IStorageGateway


class StorageService:
    def __init__(self, storage: IStorageGateway) -> None:
        self._storage = storage

    def save_file(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        return self._storage.save(fileobj, filename, content_type)


__all__ = ["StorageService"]
