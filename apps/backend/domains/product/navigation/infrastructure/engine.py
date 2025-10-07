from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


async def ensure_engine(
    container: Any, label: str = "navigation-api"
) -> AsyncEngine | None:
    """Build AsyncEngine for navigation domain using container settings."""

    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            return None
        if "?" in dsn:
            dsn = dsn.split("?", 1)[0]
        return get_async_engine(label, url=dsn, future=True)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("navigation relations: invalid database configuration: %s", exc)
        return None
    except SQLAlchemyError:
        logger.exception("navigation relations: failed to create engine")
        return None
