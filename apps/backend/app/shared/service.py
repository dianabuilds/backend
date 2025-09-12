from __future__ import annotations

"""Shared base service helpers (pure, no I/O).

This module re‑exports from ``app.common.service`` for now to ease migration.
Switch imports to ``app.shared.service`` and later remove the legacy module.
"""

import warnings

warnings.warn(
    "Prefer app.shared.service; app.common.service will be removed",
    DeprecationWarning,
    stacklevel=2,
)

try:  # pragma: no cover - transitional
    from app.common.service import *  # noqa: F401,F403
except Exception:  # pragma: no cover
    pass

