from __future__ import annotations

"""HTTP client provider shim.

Prefer importing HTTP client facilities from providers. This module re-exports
the legacy implementation from ``app.infra.http_client`` for a smooth
transition. Update imports to this module; later we will move the concrete
implementation here and remove the legacy path.
"""

import warnings

try:
   from app.providers.http_client import HttpClient, create_http_client  # noqa: F401
except Exception:  # pragma: no cover
    # Keep module importable even if legacy path changes mid-migration.
    HttpClient = object  # type: ignore
    def create_http_client(*args, **kwargs):  # type: ignore
        raise RuntimeError("HTTP client implementation not available")

warnings.warn(
    "Use app.providers.http_client; app.infra.http_client is deprecated",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["HttpClient", "create_http_client"]

