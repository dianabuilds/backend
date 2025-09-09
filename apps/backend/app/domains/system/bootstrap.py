from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def ensure_default_admin() -> None:
    """Create default admin user if necessary (no-op stub)."""
    try:
        from app.domains.auth.application.services.bootstrap import (
            ensure_default_admin as _impl,  # type: ignore
        )
    except Exception:
        logger.warning("ensure_default_admin implementation missing")
        return
    await _impl()
