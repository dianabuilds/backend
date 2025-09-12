from __future__ import annotations

"""Deprecated shim: use app.domains.ai.validation.ai.run_ai_validation."""

import warnings

from app.domains.ai.validation.ai import run_ai_validation  # noqa: F401

warnings.warn(
    "app.validation.ai is deprecated; use app.domains.ai.validation.ai",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["run_ai_validation"]
