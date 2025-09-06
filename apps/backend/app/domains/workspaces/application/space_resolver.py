from __future__ import annotations

from uuid import UUID

from app.core.settings import get_settings


def resolve_workspace_id(space_id: UUID | None, workspace_id: UUID | None = None) -> UUID | None:
    """Return effective workspace identifier based on feature flag.

    When SPACES_ENFORCED is enabled, ``space_id`` must be provided and is
    returned. Otherwise the existing ``workspace_id`` is used as a fallback.
    """
    settings = get_settings()
    if settings.spaces_enforced:
        if space_id is None:
            raise ValueError("space_id is required when SPACES_ENFORCED")
        return space_id
    return space_id or workspace_id
