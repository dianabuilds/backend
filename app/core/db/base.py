import os
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


# Import all models here so Base has them registered
# In testing mode we only import the user model to avoid configuring
# unrelated relationships which may depend on missing tables.
if os.environ.get("TESTING") == "True":
    from app.domains.users.infrastructure.models.user import User  # noqa
else:
    from app.core.idempotency_models import IdempotencyKey  # noqa
    from app.core.outbox_models import OutboxEvent  # noqa
    from app.domains.nodes.infrastructure.models.node import Node  # noqa
    from app.domains.nodes.models import NodeItem  # noqa
    from app.domains.tags.infrastructure.models.tag_models import TagAlias  # noqa
    from app.domains.tags.models import ContentTag, Tag  # noqa
    from app.domains.users.infrastructure.models.user import User  # noqa

# Add all other models here
