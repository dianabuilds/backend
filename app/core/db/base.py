from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
import os


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
    from app.domains.users.infrastructure.models.user import User  # noqa
    from app.domains.nodes.infrastructure.models.node import Node  # noqa
    from app.domains.moderation.infrastructure.models.moderation_models import (
        ContentModeration,
        UserRestriction,
    )  # noqa
    from app.domains.navigation.infrastructure.models.echo_models import (
        EchoTrace,
    )  # noqa
    from app.domains.navigation.infrastructure.models.transition_models import (
        NodeTransition,
    )  # noqa
    from app.domains.notifications.infrastructure.models.notification_models import (
        Notification,
    )  # noqa
    from app.domains.payments.infrastructure.models.payment_models import (
        PaymentGatewayConfig,
        PaymentTransaction,
    )  # noqa
    from app.core.idempotency_models import IdempotencyKey  # noqa
    from app.core.outbox_models import OutboxEvent  # noqa
    from app.domains.quests.infrastructure.models.quest_version_models import (
        QuestVersion,
        QuestGraphNode,
        QuestGraphEdge,
        DraftLock,
    )  # noqa
    from app.domains.moderation.infrastructure.models.moderation_case_models import (
        ModerationCase,
        ModerationLabel,
        CaseLabel,
        CaseNote,
        CaseAttachment,
        CaseEvent,
    )  # noqa
    from app.core.search.models import (
        ConfigVersion,
        SearchRelevanceActive,
    )  # noqa
    from app.domains.tags.infrastructure.models.tag_models import TagAlias  # noqa
    from app.domains.tags.infrastructure.models.tag_models import (
        TagMergeLog,
    )  # noqa
    from app.domains.tags.models import Tag, ContentTag  # noqa
    from app.domains.content.models import ContentItem  # noqa

# Add all other models here
