"""SQLAlchemy models package (core).

Expose the declarative Base for Alembic and import only core (non-domain) tables.
Domain models must be imported from app.domains.<domain>.infrastructure.models.
"""

from app.core.db.base import Base  # re-export Base from the DB layer

# Import core models to register them with SQLAlchemy metadata (no domain models here)
# Prefer importing modules to avoid name coupling
from . import outbox as _outbox  # noqa: F401
from . import idempotency as _idempotency  # noqa: F401
from . import search_config as _search_config  # noqa: F401
from . import event_counter as _event_counter  # noqa: F401

__all__ = ["Base"]

