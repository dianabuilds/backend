from __future__ import annotations

import warnings

from app.providers.db import (  # noqa: F401
    adapters,
    base,
    sa_adapters,
    session,
    transition_query,
)

warnings.warn(
    "app.core.db is deprecated; use app.providers.db instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "adapters",
    "base",
    "sa_adapters",
    "session",
    "transition_query",
]
