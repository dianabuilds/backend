"""Notifications domain package."""

import os

# Ensure event listeners are registered when package is imported. Skip this
# during tests to avoid importing the full application graph.
if os.environ.get("TESTING") != "True":
    try:  # pragma: no cover - best effort import
        from . import service as _service  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        _service = None
else:  # pragma: no cover
    _service = None
