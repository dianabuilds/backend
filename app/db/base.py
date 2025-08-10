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
# This is needed for Alembic and session management
from app.models.user import User  # noqa
from app.models.node import Node  # noqa
from app.models.moderation import ContentModeration, UserRestriction  # noqa
from app.models.echo_trace import EchoTrace  # noqa
from app.models.transition import NodeTransition  # noqa
from app.models.idempotency import IdempotencyKey  # noqa
from app.models.outbox import OutboxEvent  # noqa

# Add all other models here
