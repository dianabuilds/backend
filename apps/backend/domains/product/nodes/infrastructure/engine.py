from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


async def ensure_engine(container: Any, label: str = "nodes-api") -> AsyncEngine | None:
    try:
        dsn = to_async_dsn(container.settings.database_url)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("nodes api invalid database configuration", exc_info=exc)
        return None
    if not dsn:
        return None
    if "?" in dsn:
        dsn = dsn.split("?", 1)[0]
    try:
        return get_async_engine(label, url=dsn, future=True)
    except SQLAlchemyError as exc:
        logger.error("nodes api failed to create engine", exc_info=exc)
        return None
