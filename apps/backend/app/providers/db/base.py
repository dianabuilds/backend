from __future__ import annotations

from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.settings import EnvMode


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
_settings = get_settings()
if _settings.env_mode == EnvMode.test:
    from app.domains.users.infrastructure.models.user import User  # noqa
    # Minimal set of models needed for unit tests that create metadata
    # including quests and content items.
    from app.domains.nodes.infrastructure.models.node import Node  # noqa
    from app.domains.nodes.models import NodeItem  # noqa
    import app.domains.tags.models  # noqa: F401
else:
    from app.models.idempotency import IdempotencyKey  # noqa
    from app.models.outbox import OutboxEvent  # noqa
    from app.domains.nodes.infrastructure.models.node import Node  # noqa
    from app.domains.nodes.models import NodeItem  # noqa
    from app.domains.tags.infrastructure.models.tag_models import TagAlias  # noqa
    import app.domains.tags.models  # noqa: F401
    from app.domains.users.infrastructure.models.user import User  # noqa
    # AI domain models (v1 minimal + v2 system tables)
    from app.domains.ai.infrastructure.models.system_models import (  # noqa: F401
        AISystemModel,
        AIModelPrice,
        AIDefaultModel,
    )
    from app.domains.ai.infrastructure.models.ai_settings import AISettings  # noqa: F401
    from app.domains.ai.infrastructure.models.ai_system_v2 import (  # noqa: F401
        AIProvider,
        AIProviderSecret,
        AIModel,
        AIDefaults,
        AIRoutingProfile,
        AIPreset,
        AIEvalRun,
    )

# Add all other models here
