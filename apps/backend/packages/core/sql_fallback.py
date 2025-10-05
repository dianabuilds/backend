from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

try:
    from .config import to_async_dsn as _to_async_dsn
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    to_async_dsn: Callable[[Any], str] | None = None
else:
    to_async_dsn = cast(Callable[[Any], str], _to_async_dsn)

from .testing import is_test_mode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SqlBackendDecision:
    """Represents the outcome of evaluating whether SQL storage can be used."""

    dsn: str | None
    reason: str | None


_DEFAULT_DATABASE_ATTR = "database_url"


def evaluate_sql_backend(
    settings: Any,
    *,
    database_attr: str = _DEFAULT_DATABASE_ATTR,
) -> SqlBackendDecision:
    """Determine whether SQL storage can be used for the provided settings.

    Returns the normalized DSN if SQL should be used, otherwise captures the
    fallback reason so callers can log meaningful messages.
    """

    if is_test_mode(settings):
        return SqlBackendDecision(None, "test mode disallows SQL backend")

    if settings is None:
        return SqlBackendDecision(None, "settings not provided")

    if to_async_dsn is None:
        return SqlBackendDecision(None, "database helpers unavailable")

    raw_url = getattr(settings, database_attr, None)
    if raw_url in (None, ""):
        return SqlBackendDecision(None, f"{database_attr} not configured")

    try:
        dsn = to_async_dsn(raw_url)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.debug(
            "Failed to normalize database URL %r: %s",
            raw_url,
            exc,
            exc_info=True,
        )
        return SqlBackendDecision(None, f"invalid {database_attr}: {exc}")

    if not dsn:
        return SqlBackendDecision(None, f"{database_attr} normalized to empty value")

    dsn_text = str(dsn).strip()
    if not dsn_text:
        return SqlBackendDecision(None, f"{database_attr} normalized to empty value")

    return SqlBackendDecision(dsn_text, None)
