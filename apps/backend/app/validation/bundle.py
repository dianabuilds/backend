from __future__ import annotations

"""Deprecated shim: use app.domains.ai.validation.bundle.BUNDLE."""

import warnings

from app.domains.ai.validation.bundle import BUNDLE  # noqa: F401

warnings.warn(
    "app.validation.bundle is deprecated; use app.domains.ai.validation.bundle",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["BUNDLE"]
