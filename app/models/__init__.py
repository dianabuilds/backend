"""SQLAlchemy models package.

This module exposes the declarative ``Base`` used by all models and ensures
that individual model modules are imported so that ``Base.metadata`` is aware
of them.  The ``Base`` class itself lives in ``app.db.base`` which provides a
custom declarative base with automatic ``__tablename__`` generation.
"""

from app.db.base import Base  # re-export Base from the DB layer

# Import models here to register them with SQLAlchemy's metadata
from .user import User  # noqa: F401
from .node import Node  # noqa: F401

# Add future models' imports above

