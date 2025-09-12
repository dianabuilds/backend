from __future__ import annotations

import warnings

# Backwards-compatibility shim: use ports.tokens.ITokenService instead
from app.domains.auth.application.ports.tokens import (  # noqa: F401
    ITokenService,
)

warnings.warn(
    "auth.application.ports.token_port is deprecated; use auth.application.ports.tokens",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["ITokenService"]
