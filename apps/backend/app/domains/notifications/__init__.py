"""Notifications domain package."""

from app.core.policy import policy

# Ensure event listeners are registered when package is imported. Skip this
# during tests to avoid importing the full application graph.
if policy.allow_write:
    try:  # pragma: no cover - best effort import
        from . import service as _service  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        _service = None
else:  # pragma: no cover
    _service = None
