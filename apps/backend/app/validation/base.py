from __future__ import annotations

"""Deprecated shim: use app.kernel.validation.base.

This module re-exports the kernel validation engine to keep imports working
while we migrate domains to the new location.
"""

import warnings

from app.kernel.validation.base import (  # noqa: F401
    Validator,
    register,
    run_validators,
    validator,
)

warnings.warn(
    "app.validation.base is deprecated; use app.kernel.validation.base",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["Validator", "register", "validator", "run_validators"]
