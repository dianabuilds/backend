from __future__ import annotations

from uuid import UUID


async def index_content(content_id: UUID) -> None:
    """Index content item into search backend.

    This is a placeholder implementation used for tests. The real search
    integration can plug in here.
    """
    return None
