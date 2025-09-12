from __future__ import annotations

"""Shared utilities: pure, re-usable helpers without side effects.

This package contains modules that are safe to import from any domain.
Rules of thumb:
- No HTTP/DB/file I/O or network calls.
- No imports from ``app.domains.*`` or other app layers with side effects.
- OK to depend on stdlib, typing, pydantic and other pure modules.

See README in this package for detailed guidance.
"""

__all__ = []

