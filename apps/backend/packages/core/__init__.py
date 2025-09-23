from __future__ import annotations

from .api_contracts import validate_notifications_request  # noqa: F401

# Re-export commonly used primitives for convenience imports like
# `from packages.core import Flags, with_trace, validate_notifications_request`.
from .flags import Flags  # noqa: F401
from .settings_contract import (  # noqa: F401
    SETTINGS_SCHEMA_HEADER,
    SETTINGS_SCHEMA_VERSION,
    assert_if_match,
    attach_settings_schema,
    compute_etag,
    set_etag,
)
from .telemetry import setup_logging, with_trace  # noqa: F401

__all__ = [
    "Flags",
    "with_trace",
    "setup_logging",
    "validate_notifications_request",
    "attach_settings_schema",
    "compute_etag",
    "set_etag",
    "assert_if_match",
    "SETTINGS_SCHEMA_VERSION",
    "SETTINGS_SCHEMA_HEADER",
]
