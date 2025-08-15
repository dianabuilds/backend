from __future__ import annotations

from app.services.storage import LocalStorage, Storage


def get_storage() -> Storage:
    """Dependency provider for storage backend.

    Currently returns :class:`LocalStorage` but can be swapped in future.
    """
    return LocalStorage()
