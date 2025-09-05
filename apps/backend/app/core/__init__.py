from __future__ import annotations

import sys
import warnings
from importlib import import_module

_cache = import_module("app.providers.cache")
_redis_utils = import_module("app.providers.redis_utils")
_outbox = import_module("app.providers.outbox")

sys.modules[__name__ + ".cache"] = _cache
sys.modules[__name__ + ".redis_utils"] = _redis_utils
sys.modules[__name__ + ".outbox"] = _outbox

warnings.warn("Deprecated: use app.providers.cache", DeprecationWarning, stacklevel=2)
warnings.warn("Deprecated: use app.providers.outbox", DeprecationWarning, stacklevel=2)

cache = _cache
redis_utils = _redis_utils
outbox = _outbox

__all__ = ["cache", "redis_utils", "outbox"]
