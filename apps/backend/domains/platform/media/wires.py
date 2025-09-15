from __future__ import annotations

from dataclasses import dataclass

from domains.platform.media.adapters.local_storage import (
    LocalStorageGateway,
)


@dataclass
class MediaContainer:
    storage: LocalStorageGateway
    upload_dir: str


def build_container() -> MediaContainer:
    storage = LocalStorageGateway()
    return MediaContainer(storage=storage, upload_dir=str(storage.base_dir))


__all__ = ["MediaContainer", "build_container"]
