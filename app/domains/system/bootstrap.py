from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

async def ensure_default_admin() -> None:
    """Create default admin user if necessary (no-op stub)."""
    try:
        from app.domains.auth.application.services.bootstrap import ensure_default_admin as _impl  # type: ignore
    except Exception:
        logger.warning("ensure_default_admin implementation missing")
        return
    await _impl()


async def ensure_global_workspace() -> None:
    """Create global system workspace if necessary (no-op stub)."""
    try:
        from app.domains.workspaces.application.bootstrap import (
            ensure_global_workspace as _impl,
        )
    except Exception:
        logger.warning("ensure_global_workspace implementation missing")
        return
    await _impl()
