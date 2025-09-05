from __future__ import annotations

from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.
    Автоматически создает имена таблиц на основе имен классов.
    """

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


from app.core.policy import policy  # noqa: E402

# Import all models here so Base has them registered
if not policy.allow_write:
    from app.domains.users.infrastructure.models.user import User  # noqa
else:
    from app.models.idempotency import IdempotencyKey  # noqa
    from app.models.outbox import OutboxEvent  # noqa
    from app.domains.nodes.infrastructure.models.node import Node  # noqa
    from app.domains.nodes.models import NodeItem  # noqa
    from app.domains.tags.infrastructure.models.tag_models import TagAlias  # noqa
    import app.domains.tags.models  # noqa: F401
    from app.domains.users.infrastructure.models.user import User  # noqa
    from app.models import quests as _quests  # noqa: F401

# Add all other models here
