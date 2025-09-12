from __future__ import annotations

"""Shared error helpers.

This module currently re‑exports from the legacy ``app.common.errors`` to keep
the migration incremental. Prefer importing from ``app.shared.errors`` and
replace legacy imports in the codebase. Later, the implementation can be moved
fully here and ``app.common.errors`` deleted.
"""

import warnings

warnings.warn(
    "Prefer app.shared.errors; app.common.errors will be removed",
    DeprecationWarning,
    stacklevel=2,
)

try:  # pragma: no cover - transitional
    from app.common.errors import *  # noqa: F401,F403
except Exception:  # pragma: no cover
    # Keep module importable even if legacy path is already removed.
    pass

