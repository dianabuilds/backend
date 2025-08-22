from __future__ import annotations

from app.domains.media.application.ports.storage_port import IStorageGateway
from app.domains.media.infrastructure.storage.local_storage import LocalStorageGateway


def get_storage() -> IStorageGateway:
    """Dependency provider for storage backend (media domain).

    Currently returns LocalStorageGateway but can be swapped in future.
    """
    return LocalStorageGateway()
