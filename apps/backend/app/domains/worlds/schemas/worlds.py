from __future__ import annotations

"""Domain schemas for Worlds (temporary bridge).

Implementation is still sourced from the legacy path ``app.schemas.worlds``.
This file exists to provide the canonical domain import path:

    from app.domains.worlds.schemas.worlds import ...

Once all imports are migrated, the actual schema definitions should be moved
here and the legacy module removed.
"""

try:  # pragma: no cover - transitional bridge
    from app.schemas.worlds import *  # noqa: F401,F403
except Exception:  # pragma: no cover
    # If the legacy module is already gone, keep the package importable.
    pass

