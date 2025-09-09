"""Notifications domain package."""

from types import ModuleType

from app.core.config import get_settings
from app.core.settings import EnvMode

_service: ModuleType | None

# Ensure event listeners are registered when package is imported.
# Skip this during tests to avoid importing the full application graph.
_settings = get_settings()
if _settings.env_mode == EnvMode.test:
    _service = None
else:
    try:  # pragma: no cover - best effort import
        from . import service as _service  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        _service = None
