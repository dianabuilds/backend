from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class RuntimePolicy:
    """Simple runtime policy derived from environment variables."""

    allow_write: bool
    rate_limit_mode: str

    @classmethod
    def from_env(cls) -> RuntimePolicy:
        testing = os.environ.get("TESTING", "").lower() in {"true", "1", "t"}
        allow_write = not testing
        rate_limit_mode = os.environ.get("RATE_LIMIT_MODE", "disabled" if testing else "enforce")
        return cls(allow_write=allow_write, rate_limit_mode=rate_limit_mode)


policy = RuntimePolicy.from_env()
