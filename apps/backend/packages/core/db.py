from __future__ import annotations

"""DB session plumbing (placeholder).

Provide your SQLAlchemy session factory/dependency here. Kept minimal
to avoid coupling in templates.
"""

from collections.abc import AsyncIterator


async def db_session_dep() -> AsyncIterator[object]:  # pragma: no cover - placeholder
    yield None
